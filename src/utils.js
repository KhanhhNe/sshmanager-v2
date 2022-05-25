const moment = require('moment')
const _ = require('lodash')

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

    socket.send(JSON.stringify({
      last_modified: lastModified,
      ids: _.map(objectsList, item => item.id)
    }))
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

      // Update/Insert objects from database
      for (const item of data.objects) {
        const itemInList = _.find(objectsList, val => val.id === item.id)
        if (itemInList) {
          Object.assign(itemInList, item)
        } else {
          objectsList.push(item)
        }
      }

      // Remove objects that no longer in the database
      for (const itemId of data.removed) {
        const itemIndex = _.findIndex(objectsList, item => item.id === itemId)
        if (itemIndex !== -1) {
          objectsList.splice(itemIndex, 1)
        }
      }
    })

    s.addEventListener('close', () => setTimeout(connect, 1000))
  }
}

module.exports = {
  getTimeDisplay,
  getSshText,
  setupWebsocket
}
