import { createCanvas, loadImage, GlobalFonts } from '@napi-rs/canvas'
import { writeFileSync, mkdirSync, readFileSync, existsSync } from 'fs'
import { join } from 'path'

// ─── LOAD CONFIG ──────────────────────────────────────────
function loadConfig() {
    if (!existsSync('./config.json')) {
        throw new Error('config.json not found')
    }
    return JSON.parse(readFileSync('./config.json', 'utf-8'))
}

const config = loadConfig()
const OUTPUT_DIR = `${config.paths.output_dir}/${config.niche}`
const CANVAS_W = config.canvas.width
const CANVAS_H = config.canvas.height
const OVERLAY_OPACITY = config.canvas.overlay_opacity
const OVERLAY_COLOR = '0,0,0'
const FONT_PATH = config.paths.font_path
const FONT_NAME = config.text.font_name
const CONFIG_FILE = config.paths.config_file

// ─── LOAD FONT ────────────────────────────────────────────
if (!existsSync(FONT_PATH)) {
    throw new Error(`Font file not found: ${FONT_PATH}`)
}
GlobalFonts.registerFromPath(FONT_PATH, FONT_NAME)

// ─── LOAD SLIDE CONFIG ────────────────────────────────────
if (!existsSync(CONFIG_FILE)) {
    throw new Error(`Config file not found: ${CONFIG_FILE}`)
}
const slides = JSON.parse(readFileSync(CONFIG_FILE, 'utf-8'))

// ─── HELPERS ──────────────────────────────────────────────
function wrapText(ctx, text, maxWidth) {
    const words = text.split(' ')
    const lines = []
    let current = ''
    for (const word of words) {
        const test = current ? `${current} ${word}` : word
        if (ctx.measureText(test).width > maxWidth && current) {
            lines.push(current)
            current = word
        } else {
            current = test
        }
    }
    if (current) lines.push(current)
    return lines
}

async function generateSlide(slide, index) {
    try {
        if (!existsSync(slide.imagePath)) {
            throw new Error(`Image not found: ${slide.imagePath}`)
        }
        
        const canvas = createCanvas(CANVAS_W, CANVAS_H)
        const ctx = canvas.getContext('2d')
        
        ctx.imageSmoothingEnabled = true
        ctx.imageSmoothingQuality = 'high'

        // 1. Draw background image, cover-fit
        const img = await loadImage(slide.imagePath)
        const scale = Math.max(CANVAS_W / img.width, CANVAS_H / img.height)
        const drawW = img.width * scale
        const drawH = img.height * scale
        const offsetX = (CANVAS_W - drawW) / 2
        const offsetY = (CANVAS_H - drawH) / 2
        ctx.drawImage(img, offsetX, offsetY, drawW, drawH)

        // 2. Dark overlay
        ctx.fillStyle = `rgba(${OVERLAY_COLOR},${OVERLAY_OPACITY})`
        ctx.fillRect(0, 0, CANVAS_W, CANVAS_H)

        // 3. Draw each line of text
        const PADDING = 80
        const MAX_TEXT_W = CANVAS_W - PADDING * 2

        const allWrappedLines = []
        for (const line of slide.lines) {
            ctx.font = `${line.size}px ${FONT_NAME}`
            const wrapped = wrapText(ctx, line.text, MAX_TEXT_W)
            wrapped.forEach(l => {
                allWrappedLines.push({ text: l, size: line.size })
            })
        }

        let totalHeight = 0
        allWrappedLines.forEach(l => {
            totalHeight += l.size * 1.3
        })

        let currentY = (CANVAS_H - totalHeight) / 2 + (allWrappedLines[0] ? allWrappedLines[0].size : 72) / 2

        for (const l of allWrappedLines) {
            ctx.font = `${l.size}px ${FONT_NAME}`
            ctx.fillStyle = '#ffffff'
            ctx.textAlign = 'center'
            ctx.textBaseline = 'middle'

            ctx.shadowColor = 'rgba(255, 255, 255, 1)'
            ctx.shadowBlur = config.canvas.glow_blur_radius
            ctx.shadowOffsetY = 0

            ctx.fillText(l.text, CANVAS_W / 2, currentY)
            currentY += l.size * 1.3
        }

        // 4. Export PNG
        mkdirSync(OUTPUT_DIR, { recursive: true })
        const outPath = join(OUTPUT_DIR, `slide_${String(index + 1).padStart(2, '0')}.png`)
        const buffer = canvas.toBuffer('image/png')
        writeFileSync(outPath, buffer)
        console.log(`✓ ${outPath}`)
        return outPath
    } catch (error) {
        console.error(`❌ Error generating slide ${index + 1}: ${error.message}`)
        throw error
    }
}

// ─── MAIN ─────────────────────────────────────────────────
async function main() {
    try {
        if (!slides || slides.length === 0) {
            throw new Error(`No slides found in ${CONFIG_FILE}`)
        }
        
        console.log(`Generating ${slides.length} slides to ${OUTPUT_DIR}...`)
        
        const results = []
        for (let i = 0; i < slides.length; i++) {
            const path = await generateSlide(slides[i], i)
            results.push(path)
        }
        
        console.log(`\n✅ Generated ${results.length} slides`)
        console.log(`📂 Output: ${OUTPUT_DIR}/`)
        process.exit(0)
    } catch (error) {
        console.error(`❌ Error: ${error.message}`)
        process.exit(1)
    }
}

main()
