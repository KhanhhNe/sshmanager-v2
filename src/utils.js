const moment = require('moment')


/**
 * Parse a date string and return time string in format HH:MM:SS
 * @param timeString
 * @returns {string}
 */
function getTimeDisplay(timeString) {
    if (timeString) {
        return new moment(timeString).fromNow(true)
    } else {
        return ''
    }
}


/**
 * Get SSH display text, in format of status|ip|username|password
 * @param ssh SSH object
 * @returns {string} SSH display text
 */
function getSshText(ssh) {
    return `${ssh.status_text}|${ssh.ip}|${ssh.username}|${ssh.password}`
}


module.exports = {
    getTimeDisplay,
    getSshText
}