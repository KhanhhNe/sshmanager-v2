const moment = require('moment')
const _ = require("lodash");


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


function setupWebsocket(objectsList, endpoint) {
    let socket, updateInterval
    let lastModified = null
    let updateReceived = true
    connect()

    function connect() {
        try {
            if (socket) socket.close()
            socket = new WebSocket(endpoint)
            addListeners(socket)
        } catch (e) {
            console.error(e)
            setTimeout(connect, 1000)
        }
    }

    function requestUpdate() {
        if (socket.readyState !== WebSocket.OPEN) return

        if (updateReceived) {
            socket.send(JSON.stringify({
                last_modified: lastModified,
                ids: _.map(objectsList, item => item.id)
            }))
            updateReceived = false
        }
    }

    function updateObjects(data) {
        const indexes = {}
        for (const item of data.objects) {
            indexes[item.id] = undefined
        }

        // Build indexes from item ID to list index
        for (const [index, item] of Object.entries(objectsList)) {
            if (item.id in indexes) {
                indexes[item.id] = index
            }
        }

        // Update/insert items
        for (const item of data.objects) {
            const index = indexes[item.id]
            if (index) {
                Object.assign(objectsList[index], item)
            } else {
                objectsList.push(item)
            }
        }

        // Remove items marked for removal
        objectsList = _.filter(objectsList, item => _.find(data.removed, i => i.id === item.id))
    }

    function addListeners(s) {
        s.addEventListener('open', function () {
            requestUpdate()
            clearInterval(updateInterval)
            updateInterval = setInterval(requestUpdate, 200)
        })

        s.addEventListener('message', function (event) {
            const data = JSON.parse(event.data)
            lastModified = data.last_modified || lastModified

            // Upate objects from database
            updateObjects(data)
            updateReceived = true
        })

        s.addEventListener('close', () => setTimeout(connect, 1000))
    }
}


module.exports = {
    getTimeDisplay,
    getSshText,
    setupWebsocket
}