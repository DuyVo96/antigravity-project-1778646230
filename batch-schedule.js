// batch-schedule.js
// Reads schedule.json, uploads each slide set, schedules via Postiz Agent CLI
import { execSync } from 'child_process';
import { readFileSync, existsSync, mkdirSync, appendFileSync } from 'fs';
import { join } from 'path';

// Load config
const config = JSON.parse(readFileSync('./config.json', 'utf-8'))
const INTEGRATION_ID = process.env.TIKTOK_INTEGRATION_ID
const MAX_RETRIES = config.download.retry_max_attempts || 3

// Setup logging
const logDir = config.logging.log_dir
if (!existsSync(logDir)) mkdirSync(logDir, { recursive: true })
const logFile = join(logDir, `schedule-${new Date().toISOString().slice(0, 10)}.log`)

function log(level, message) {
    const timestamp = new Date().toISOString()
    const logEntry = `[${timestamp}] [${level}] ${message}\n`
    console.log(logEntry.trim())
    appendFileSync(logFile, logEntry)
}

function validateSchedule() {
    const scheduleFile = config.paths.schedule_file
    if (!existsSync(scheduleFile)) {
        throw new Error(`Schedule file not found: ${scheduleFile}`)
    }
    
    let schedule
    try {
        schedule = JSON.parse(readFileSync(scheduleFile, 'utf-8'))
    } catch (e) {
        throw new Error(`Invalid JSON in ${scheduleFile}: ${e.message}`)
    }
    
    if (!Array.isArray(schedule)) {
        throw new Error(`Schedule must be an array, got ${typeof schedule}`)
    }
    
    if (schedule.length === 0) {
        throw new Error(`Schedule is empty`)
    }
    
    schedule.forEach((post, i) => {
        if (!post.slides || !Array.isArray(post.slides) || post.slides.length === 0) {
            throw new Error(`Post ${i} missing slides array or empty`)
        }
        if (!post.caption || typeof post.caption !== 'string') {
            throw new Error(`Post ${i} missing caption`)
        }
        if (!post.scheduledAt) {
            throw new Error(`Post ${i} missing scheduledAt timestamp`)
        }
    })
    
    return schedule
}

function uploadSlideWithRetry(slide, attempt = 1) {
    try {
        const rawOutput = execSync(`postiz upload ${slide}`, { encoding: 'utf-8' })
        const jsonMatch = rawOutput.substring(rawOutput.indexOf('{'), rawOutput.lastIndexOf('}') + 1)
        const result = JSON.parse(jsonMatch)
        
        if (!result.path) {
            throw new Error(`Upload response missing 'path' field`)
        }
        
        log('info', `✓ Uploaded: ${slide} → ${result.path}`)
        return result.path
    } catch (error) {
        if (attempt < MAX_RETRIES) {
            log('warn', `Upload failed for ${slide} (attempt ${attempt}/${MAX_RETRIES}): ${error.message}. Retrying...`)
            return uploadSlideWithRetry(slide, attempt + 1)
        }
        throw new Error(`Failed to upload ${slide} after ${MAX_RETRIES} attempts: ${error.message}`)
    }
}

async function main() {
    try {
        if (!INTEGRATION_ID) {
            throw new Error('TIKTOK_INTEGRATION_ID environment variable not set')
        }
        
        const schedule = validateSchedule()
        log('info', `Starting schedule processing for ${schedule.length} posts`)
        
        for (const [postIdx, post] of schedule.entries()) {
            try {
                log('info', `Processing post ${postIdx + 1}/${schedule.length}: ${post.slides.length} slides`)
                
                // 1. Upload each PNG slide with retry logic
                const slideUrls = []
                for (const slide of post.slides) {
                    const url = uploadSlideWithRetry(slide)
                    slideUrls.push(url)
                }
                
                const slideFlags = `-m "${slideUrls.join(',')}"`
                
                // 2. Prepare TikTok settings
                const tiktokSettings = JSON.stringify(config.postiz)
                
                // 3. Escape caption safely (prevent shell interpretation)
                const safeCaption = post.caption.replace(/\$/g, '\\$')
                
                // 4. Schedule via Postiz
                log('info', `Scheduling post ${postIdx + 1} for ${post.scheduledAt}`)
                execSync(
                    `postiz posts:create \
                  -c "${safeCaption}" \
                  ${slideFlags} \
                  -s "${post.scheduledAt}" \
                  -i "${INTEGRATION_ID}" \
                  --settings '${tiktokSettings}'`,
                    { stdio: 'inherit', encoding: 'utf-8' }
                )
                
                log('info', `✓ Scheduled post ${postIdx + 1}: ${post.slides.length} slides at ${post.scheduledAt}`)
            } catch (postError) {
                log('error', `Failed to process post ${postIdx + 1}: ${postError.message}`)
                throw postError
            }
        }
        
        log('info', `✅ Successfully scheduled all ${schedule.length} posts`)
        process.exit(0)
    } catch (error) {
        log('error', `❌ Fatal error: ${error.message}`)
        console.error(error)
        process.exit(1)
    }
}

main()
