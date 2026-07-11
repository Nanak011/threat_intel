const fs = require('fs');

const INPUT_FEED_URL = 'https://raw.githubusercontent.com/Nanak011/threat_intel/main/threat_feed.json';
const OUTPUT_FILE = 'threat_feed_resolved.json';
const REQUEST_DELAY = 1100; // 1.1s safe pace for 60 RPM rules

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function resolveIP(ip, attempt = 1) {
    try {
        const res = await fetch(`https://free.freeipapi.com/api/json/${ip}`);
        
        if (res.status === 429) {
            const waitTime = Math.pow(2, attempt) * 5000; 
            console.warn(`[!] Rate limited (429) on ${ip}. Cooling down for ${waitTime / 1000}s (Attempt ${attempt}/5)...`);
            await sleep(waitTime);
            return await resolveIP(ip, attempt + 1);
        }

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        
        const geo = await res.json();
        return {
            latitude: geo.latitude || null,
            longitude: geo.longitude || null,
            cityName: geo.cityName || 'Unknown',
            countryName: geo.countryName || 'Unknown'
        };
    } catch (err) {
        if (attempt <= 5) {
            await sleep(3000);
            return await resolveIP(ip, attempt + 1);
        }
        console.error(`[-] Permanently failed to resolve IP: ${ip}`, err.message);
        return null;
    }
}

async function main() {
    console.log('[*] Fetching raw threat intel feed...');
    const response = await fetch(INPUT_FEED_URL);
    const rawData = await response.json();
    
    const uniqueIps = [...new Set(rawData.map(item => item.ip))];
    console.log(`[*] Found ${rawData.length} total rows. Extracted ${uniqueIps.length} strict UNIQUE IPs.`);

    let resolvedList = [];
    let processedIps = new Set();

    // CHECK IF PROGRESS FILE EXISTS TO RESUME
    if (fs.existsSync(OUTPUT_FILE)) {
        try {
            console.log(`[*] Found existing file: ${OUTPUT_FILE}. Checking history...`);
            let fileContent = fs.readFileSync(OUTPUT_FILE, 'utf-8').trim();
            
            // Clean up missing closing bracket if previous run crashed/stopped midway
            if (!fileContent.endsWith(']')) {
                fileContent += '\n]';
            }

            resolvedList = JSON.parse(fileContent);
            resolvedList.forEach(entry => {
                if (entry && entry.ip) processedIps.add(entry.ip);
            });
            console.log(`[+] Found ${processedIps.size} already resolved IPs. Resuming from last progress checkpoint.`);
        } catch (e) {
            console.warn(`[!] Existing file corrupt or unreadable. Starting clean execution.`);
            resolvedList = [];
            processedIps = new Set();
        }
    }

    // Filter down to ONLY the IPs we haven't seen yet
    const remainingIps = uniqueIps.filter(ip => !processedIps.has(ip));
    console.log(`[*] Total IPs to process in this run: ${remainingIps.length}`);

    // Process new unique IPs sequentially
    for (let i = 0; i < remainingIps.length; i++) {
        const ip = remainingIps[i];
        console.log(`[*] [Progress: ${i + 1}/${remainingIps.length}] Resolving: ${ip}`);
        
        const geo = await resolveIP(ip);
        if (geo) {
            const resolvedEntry = {
                ip: ip,
                latitude: geo.latitude,
                longitude: geo.longitude,
                cityName: geo.cityName,
                countryName: geo.countryName
            };

            // Push to memory array
            resolvedList.push(resolvedEntry);

            // Overwrite cleanly with the full array so the file is ALWAYS openable and valid JSON
            fs.writeFileSync(OUTPUT_FILE, JSON.stringify(resolvedList, null, 2));
        }
        
        await sleep(REQUEST_DELAY); 
    }

    console.log(`\n[+] Checkpoint synced. Saved ${resolvedList.length} total unique profiles to: ${OUTPUT_FILE}`);
}

main();