const fs = require('fs')
const path = require('path')

function createLogger(botName) {
    const logsDir = path.join(process.cwd(), 'logs')
    if (!fs.existsSync(logsDir)) {
        fs.mkdirSync(logsDir, { recursive: true })
    }

    const logFile = path.join(logsDir, `${botName.toLowerCase()}.log`)

    function formatLine(level, message) {
        const timestamp = new Date().toISOString()
        return `[${timestamp}] [${botName}] [${level}] ${message}`
    }

    function write(level, message) {
        const line = formatLine(level, message)
        console.log(line)
        fs.appendFileSync(logFile, line + '\n', 'utf8')
    }

    return {
        info: (msg) => write('INFO', msg),
        warn: (msg) => write('WARN', msg),
        error: (msg) => write('ERROR', msg),
    }
}

module.exports = { createLogger }