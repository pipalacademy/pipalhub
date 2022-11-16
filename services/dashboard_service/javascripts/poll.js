// EDIT THIS.
const jupyterhub_url = "https://beta-test.pipal.in"

const dashboard_url = jupyterhub_url + "/services/dashboard"
const events_endpoint = dashboard_url + "/events"

function waitForUpdate(filters, interval=2000) {
    return new Promise((resolve, reject) => {
        let intervalID;
        new Promise((resolve, reject) => {
            var lastFetched = new Date();
            intervalID = setInterval(() => {
                isUpdateAvailable(filters, lastFetched)
                    .then(update => {
                        let {available, event} = update
                        if (available) {
                            resolve(event)
                        }
                    })
            }, interval)
        }).then(event => {
            clearInterval(intervalID)
            resolve(event)
        }).catch(err => {
            reject(err)
        })
    })
}

async function isUpdateAvailable(filters, lastFetched) {
    let events = await getEvents(filters)
    console.log("events", JSON.stringify(events, null, 2))

    let latestEvent = events.reduce(
        (max, current) => {
            if (max === null) {
                return current
            } else {
                let maxTs = Date.parse(max.timestamp)
                let currentTs = Date.parse(current.timestamp)
                return currentTs > maxTs ? current : max
            }
        },
        null
    )

    if (!latestEvent) {
        return {available: false, event: null}
    } else {
        let latestTimestamp = Date.parse(latestEvent.timestamp)
        return latestTimestamp > lastFetched ? {available: true, event: latestEvent} : {available: false, event: null}
    }
}

async function getEvents(filters) {
    let url = events_endpoint + "?" + new URLSearchParams(filters)
    let response = await fetch(url)
    if (response.ok) {
        return await response.json()
    } else {
        throw Error(`Server returned non-OK response code: ${response.status}`)
    }
}
