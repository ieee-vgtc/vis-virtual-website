const fs = require("fs");
const path = require("path");

// __dirname is automatically available in CommonJS
const filePath = path.join(__dirname, "../sitedata/2025/session_list.json");

const data = JSON.parse(fs.readFileSync(filePath, "utf8"))

const map = new Map()
Object.entries(data).forEach(([key,value]) => {
  value.sessions.forEach((session) => {
    if(!map.has(session.track)) {
      map.set(session.track, session.room_name)
    }
    else if(map.get(session.track) !== session.room_name) {
      throw new Error(`Expected ${session.track} to map to ${map.get(session.track)} but got ${session.room_name}`)
    }
  })
})
for (const [key, value] of map) {
  console.log(`"${key}": ${value}`);
}