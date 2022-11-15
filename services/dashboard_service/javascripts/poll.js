// EDIT THIS.
const jupyterhub_url = "https://beta-test.pipal.in"


const dashboard_url = jupyterhub_url + "/services/dashboard"
const events_endpoint = dashboard_url + "/events"

function waitForUpdate(filters, interval=2000) {
    return new Promise((resolve, reject) => {
        var lastFetched = null;
        setInterval(() => {
            isUpdateAvailable(filters, lastFetched)
                .then((available, event) => {
                    if (available && !lastFetched) {
                        lastFetched = event;
                    } else if (available) {
                        // HERE, action to do when update is available
                        console.log("new event", JSON.stringify(event))
                        alert("update is available")
                    }
                })
        }, interval)
    })
}

async function isUpdateAvailable(filters, lastFetched) {
    let events = await getEvents(filters)

    let latestEvent = events.reduce(
        (max, current) => {
            if (max === null) {
                return current
            } else {
                let maxTs = Date.parse(max.timestamp)
                let currentTs = Date.parse(current.timestamp)
                return currentTs > maxTs ? currentTs : maxTs
            }
        },
        null
    )

    if (!lastFetched) {
        return (true, latestEvent)
    }

    if (!latestEvent) {
        return (false, lastFetched)
    }

    let latestTimestamp = Date.parse(latestEvent.timestamp)
    let lastFetchedTimestamp = Date.parse(lastFetched.timestamp)

    return latestTimestamp > lastFetchedTimestamp ? (true, latestEvent) : (false, lastFetched)
}

async function getEvents(filters) {
    let response = await fetch(events_endpoint)
    if (!response.ok) {
        console.error(JSON.stringify(await response.json(), null, 2))
        throw Error("Server returned non-OK response code", response.status)
    } else {
        return await response.json()
    }
}

