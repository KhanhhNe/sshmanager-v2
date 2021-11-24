const moment = require('moment')


/**
 * Parse a date string and return time string in format HH:MM:SS
 * @param timeString
 * @returns {string}
 */
function getTimeDisplay(timeString) {
    return new moment(timeString).fromNow(true)
}


/**
 * Compare 2 SSH objects by IP, username and password
 * @param ssh SSH object
 * @param otherSSH SSH object
 */
function isSameSSH(ssh, otherSSH) {
    return (
        ssh.ip === otherSSH.ip &&
        ssh.username === otherSSH.username &&
        ssh.password === otherSSH.password)
}


/**
 * Get SSH display text, in format of status|ip|username|password
 * @param ssh SSH object
 * @returns {string} SSH display text
 */
function getSshText(ssh) {
    const liveStatus = ssh.is_live ? 'live' : 'die'
    return `${liveStatus}|${ssh.ip}|${ssh.username}|${ssh.password}`
}


/**
 * Check whether the SSH is in list or not
 * @param ssh SSH object
 * @param sshList SSH list to find
 * @returns {boolean}
 */
function isInList(ssh, sshList) {
    for (const s of sshList) {
        if (isSameSSH(s, ssh))
            return true
    }
    return false
}


/**
 * Read a file as text
 * @param file File object
 * @returns {Promise<String>}
 */
function readFileAsText(file) {
    const reader = new FileReader()
    return new Promise(resolve => {
        reader.addEventListener('load', event => {
            resolve(event.target.result)
        })
        reader.readAsText(file)
    })
}


module.exports = {
    getTimeDisplay,
    isSameSSH,
    getSshText,
    isInList,
    readFileAsText
}