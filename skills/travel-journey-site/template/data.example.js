/* Trip data for the journey engine. Everything trip-specific lives here.
   Distances are computed from coordinates at runtime; fares/timings below were
   checked against public sources in Sept 2026 (see `sources`). */
window.TRIP = {
  title: "Agra · Delhi · Varanasi",
  tagline: "Same roads, new perspective",
  subtitle: "9 nights · 10 days · three cities · a thousand stories",
  home: { id: "blr", name: "Bangalore", lat: 12.9716, lng: 77.5946, airport: { name: "Kempegowda Intl (BLR)", lat: 13.1989, lng: 77.7068 } },
  currency: { code: "INR", symbol: "₹", usd: 84 },
  defaultStart: "2026-11-28", // Sat 28 Nov → Mon 7 Dec: winter, smog season
  travellers: 2,

  cities: {
    agra: { name: "Agra", state: "Uttar Pradesh", lat: 27.1767, lng: 78.0081, accent: "#f28c28", days: "Days 1–2",
      hub: { name: "Agra Cantt station", lat: 27.1567, lng: 77.9925 },
      stay: { name: "Taj Ganj / Fatehabad Rd", lat: 27.1650, lng: 78.0450 },
      traffic: { speeds: [38,38,38,38,38,36,32,28,22,22,24,26,26,26,26,24,22,20,20,22,28,32,36,38], note: "Compact city. Cars stop 500 m short of the Taj; the last stretch is on foot or e-rickshaw. Fatehabad Road slows 17:00–20:00." },
      ride: { base: 40, perKm: 12, perMin: 1.2, min: 80, peak: 1.4 },
      climate: { hi: [19.3,25.3,30.3,37.4,39.3,38.2,33.3,32.5,32.6,32.0,27.1,21.8], lo: [7.9,12.3,16.8,22.8,25.9,28.1,26.6,26.0,25.0,20.9,14.9,10.3], rain: [27,14,24,2,21,144,209,240,214,26,2,14] },
      aqi: [4,3,3,2,2,2,1,1,1,3,5,4], // 1 good … 5 very poor (seasonal typical)
      air: { monthly: [230,170,150,160,150,120,70,60,80,150,240,210], fog: [3,2,0,0,0,0,0,0,0,0,2,3], note: "Agra sits downwind of Delhi's plume. Winter mornings bring smog and, from mid-December, dense fog that can hide the Taj until 09:00–10:00. Keep the afternoon free as a second attempt." }
    },
    delhi: { name: "Delhi", state: "NCT", lat: 28.6139, lng: 77.2090, accent: "#3aa7b8", days: "Days 3–6",
      hub: { name: "IGI Airport T3 (DEL)", lat: 28.5562, lng: 77.1000 },
      rail: { name: "Hazrat Nizamuddin (NZM)", lat: 28.5883, lng: 77.2545 },
      rail2: { name: "New Delhi (NDLS)", lat: 28.6425, lng: 77.2197 },
      stay: { name: "Connaught Place", lat: 28.6315, lng: 77.2167 },
      traffic: { speeds: [42,42,42,42,40,36,30,24,18,18,20,24,26,26,25,24,20,16,15,16,22,30,36,40], note: "TomTom Traffic Index 2025 ranks Delhi 23rd most congested worldwide; average speed 21.9 km/h. Peaks 08:00–11:00 and 17:00–21:00. Metro beats cars on any hop over 10 km at peak." },
      ride: { base: 60, perKm: 14, perMin: 1.5, min: 100, peak: 1.7 },
      climate: { hi: [18.6,24.4,29.5,36.3,38.6,37.9,33.6,32.7,33.2,31.9,27.1,22.0], lo: [7.6,12.0,16.4,22.2,25.6,27.6,26.4,26.1,25.0,20.7,15.2,10.3], rain: [23,19,32,6,26,121,265,182,188,14,4,13] },
      aqi: [5,4,3,3,3,2,1,1,2,4,5,5],
      air: { monthly: [330,250,180,190,180,150,90,80,110,220,360,300], fog: [3,1,0,0,0,0,0,0,0,0,1,3], note: "November is the worst month of the year: stubble smoke plus winter inversion push the daily CPCB AQI past 350. December 2025 averaged 294, the cleanest December on record, and still 'poor'. GRAP curbs can restrict older diesel cabs. Midday is the cleanest window." }
    },
    varanasi: { name: "Varanasi", state: "Uttar Pradesh", lat: 25.3176, lng: 82.9739, accent: "#e0b45a", days: "Days 7–8",
      hub: { name: "Lal Bahadur Shastri Airport (VNS)", lat: 25.4524, lng: 82.8593 },
      rail: { name: "Varanasi Jn (BSB)", lat: 25.3283, lng: 82.9868 },
      stay: { name: "Assi Ghat", lat: 25.2880, lng: 83.0060 },
      traffic: { speeds: [30,30,30,30,30,28,24,20,16,15,16,18,18,18,18,16,14,12,12,14,18,24,28,30], note: "The old city is car-free in practice: cabs drop at Godowlia or Assi crossing and you walk 5–15 minutes. Airport is 25 km out on the ring road, 40–75 minutes." },
      ride: { base: 40, perKm: 13, perMin: 1.2, min: 80, peak: 1.4 },
      climate: { hi: [21.0,26.8,32.0,38.0,39.4,39.5,33.6,32.2,32.4,31.1,27.9,23.1], lo: [9.8,14.0,18.4,23.8,26.7,28.9,27.0,26.1,25.9,22.6,16.8,12.2], rain: [10,16,20,3,21,123,341,303,227,95,8,14] },
      aqi: [4,3,3,2,2,2,1,1,1,3,4,4],
      air: { monthly: [210,160,130,140,130,110,70,60,80,130,220,190], fog: [3,2,0,0,0,0,0,0,0,0,1,2], note: "The river helps: mornings on the water are hazier than they look in photos, but the ghats clear by late morning. Evening aarti smoke plus winter haze make the 18:00 hour the day's worst." }
    }
  },
  /* winter hourly AQI multiplier: inversion overnight, cleanest early afternoon */
  airHourly: [1.25,1.3,1.3,1.3,1.3,1.3,1.32,1.35,1.35,1.28,1.12,.98,.85,.76,.7,.7,.76,.86,1.0,1.1,1.15,1.2,1.25,1.25],
  homeClimate: { hi: [27.6,30.9,33.0,34.6,31.3,29.1,27.1,27.9,27.8,27.9,27.2,26.8], lo: [15.9,17.2,19.5,21.1,21.2,20.4,20.0,19.7,19.5,19.3,18.4,17.2] },

  sights: [
    { id: "taj", city: "agra", name: "Taj Mahal", lat: 27.1751, lng: 78.0421, fee: [250, 1500], feeNote: "₹50 entry + ₹200 mausoleum (Indians); ₹1,300 + ₹200 (foreigners)", hours: "Sunrise to sunset", closed: "Friday", dur: 150, blurb: "The marble changes colour with the light: grey before dawn, rose at sunrise, blinding white by mid-morning. Be at the East Gate before it opens." },
    { id: "fort", city: "agra", name: "Agra Fort", lat: 27.1795, lng: 78.0211, fee: [50, 650], hours: "Sunrise to sunset", closed: "Open daily", dur: 120, blurb: "A red sandstone city within a city. From the Musamman Burj, Shah Jahan watched the Taj through the last years of his life." },
    { id: "mehtab", city: "agra", name: "Mehtab Bagh", lat: 27.1800, lng: 78.0426, fee: [25, 300], hours: "Sunrise to sunset", closed: "Open daily", dur: 60, blurb: "The moonlight garden across the river, laid out on the Taj's axis. The quiet side, and the sunset side." },
    { id: "sikri", city: "agra", name: "Fatehpur Sikri", lat: 27.0945, lng: 77.6679, fee: [50, 610], hours: "Sunrise to sunset", closed: "Open daily", dur: 150, optional: true, blurb: "Akbar's abandoned capital, 40 km west. Courtyards of red sandstone, the Buland Darwaza, and almost no one living there since 1585." },
    { id: "gate", city: "delhi", name: "India Gate", lat: 28.6129, lng: 77.2295, fee: [0, 0], hours: "Always open", closed: "Never", dur: 45, blurb: "A war memorial arch at the end of the ceremonial axis. Delhi comes here to eat ice cream after dark." },
    { id: "redfort", city: "delhi", name: "Red Fort", lat: 28.6562, lng: 77.2410, fee: [35, 550], hours: "09:30–16:30", closed: "Monday", dur: 150, blurb: "The Mughal seat of power for two centuries. Walk from the Lahori Gate through the covered bazaar into the audience halls." },
    { id: "jama", city: "delhi", name: "Jama Masjid", lat: 28.6507, lng: 77.2334, fee: [0, 0], feeNote: "Free; ₹300 camera fee; ₹100 minaret climb", hours: "07:00–12:00, 13:30–18:30", closed: "Fridays around noon prayers", dur: 60, blurb: "India's largest mosque, by the builder of the Taj. Climb the southern minaret for the best view of Old Delhi." },
    { id: "chowk", city: "delhi", name: "Chandni Chowk", lat: 28.6506, lng: 77.2303, fee: [0, 0], hours: "Shops 10:00–20:00", closed: "Sunday (most shops)", dur: 120, blurb: "The old city's main artery. Parathas, jalebi, spices, wedding silk and a few million people." },
    { id: "humayun", city: "delhi", name: "Humayun's Tomb", lat: 28.5933, lng: 77.2507, fee: [35, 550], hours: "Sunrise to sunset", closed: "Open daily", dur: 90, blurb: "The garden tomb the Taj learned from. Persian symmetry, red sandstone, and blessedly few crowds." },
    { id: "qutub", city: "delhi", name: "Qutub Minar", lat: 28.5245, lng: 77.1855, fee: [35, 550], hours: "Sunrise to sunset", closed: "Open daily", dur: 90, blurb: "A 73-metre victory tower from 1193. The iron pillar in the courtyard has not rusted in 1,600 years." },
    { id: "lotus", city: "delhi", name: "Lotus Temple", lat: 28.5535, lng: 77.2588, fee: [0, 0], hours: "09:00–17:30", closed: "Monday", dur: 60, blurb: "Twenty-seven marble petals and total silence inside. Open to everyone, of any faith or none." },
    { id: "aarti", city: "varanasi", name: "Ganga Aarti", lat: 25.3073, lng: 83.0104, fee: [0, 0], feeNote: "Free from the steps; shared boat ₹250 pp, private rowboat from ₹1,500", hours: "Daily at sunset (18:00–19:00)", closed: "Never", dur: 75, blurb: "Every evening at Dashashwamedh Ghat, priests raise tiered lamps to the river while the crowd floats candles on the water." },
    { id: "kashi", city: "varanasi", name: "Kashi Vishwanath", lat: 25.3109, lng: 83.0107, fee: [0, 0], feeNote: "Free; Sugam darshan ₹300", hours: "04:00–23:00", closed: "Never", dur: 90, blurb: "The golden-spired temple at the heart of the old city, one of the twelve Jyotirlingas. No phones or bags inside." },
    { id: "sarnath", city: "varanasi", name: "Sarnath", lat: 25.3812, lng: 83.0244, fee: [25, 300], feeNote: "ASI site ₹25/₹300; museum ₹5 extra", hours: "Sunrise to sunset; museum 09:00–17:00", closed: "Museum closed Friday", dur: 150, blurb: "Where the Buddha gave his first sermon, ten kilometres north. Deer park, the Dhamek stupa, and a very good museum." },
    { id: "ghats", city: "varanasi", name: "Ghats & Old City", lat: 25.2880, lng: 83.0060, fee: [0, 0], feeNote: "Sunrise boat ₹300 pp shared", hours: "Always", closed: "Never", dur: 180, blurb: "Eighty-four ghats in a crescent along the river. Walk them at dawn from Assi to Dashashwamedh, then get lost in the lanes behind." }
  ],

  /* Inter-city legs. `options` are alternatives the user can pick; the first is default. */
  legs: [
    { id: "L0", from: "blr", to: "delhi", day: 0, options: [
      { mode: "flight", name: "IndiGo / Air India · BLR → DEL", dep: "09:30", arr: "12:20", mins: 170, fare: [7178, 9795], note: "~800 flights a week on this route. Book 3+ weeks out for the low end.", fromPt: "homeAirport", toPt: "hub" }
    ]},
    { id: "L1", from: "delhi", to: "agra", day: 1, options: [
      { mode: "train", name: "12050 Gatimaan Express · NZM → AGC", dep: "08:10", arr: "09:50", mins: 100, fare: [993, 1495], classes: ["AC Chair Car", "Executive"], note: "Runs daily except Friday. 130 km/h, meal included. Book 60 days ahead.", fromPt: "rail", toPt: "hub" },
      { mode: "car", name: "Cab via Yamuna Expressway", dep: "07:00", arr: "10:30", mins: 210, fare: [3500, 4500], note: "Door to door, 233 km. Tolls ~₹500 included in typical quotes.", fromPt: "stay", toPt: "stay" }
    ]},
    { id: "L2", from: "agra", to: "delhi", day: 2, options: [
      { mode: "train", name: "12049 Gatimaan Express · AGC → NZM", dep: "17:50", arr: "19:30", mins: 100, fare: [993, 1495], classes: ["AC Chair Car", "Executive"], note: "Same train back. Leaves after Fatehpur Sikri with time to spare.", fromPt: "hub", toPt: "rail" }
    ]},
    { id: "L3", from: "delhi", to: "varanasi", day: 6, options: [
      { mode: "flight", name: "IndiGo / Air India · DEL → VNS", dep: "17:30", arr: "18:55", mins: 85, fare: [4733, 6786], note: "10+ daily flights. Air India, IndiGo, Akasa, Air India Express.", fromPt: "hub", toPt: "hub" },
      { mode: "train", name: "22436 Vande Bharat · NDLS → BSB", dep: "06:00", arr: "14:00", mins: 480, fare: [1440, 2925], classes: ["AC Chair Car", "Executive"], note: "759 km in 8 hours, six days a week. Costs Day 6 in Delhi but lands you at the ghats by mid-afternoon.", fromPt: "rail2", toPt: "rail" }
    ]},
    { id: "L4", from: "varanasi", to: "blr", day: 9, options: [
      { mode: "flight", name: "IndiGo · VNS → BLR", dep: "11:40", arr: "14:20", mins: 160, fare: [6603, 8231], note: "Up to 4 non-stops a day. Leave the ghats 3 hours before departure.", fromPt: "hub", toPt: "homeAirport" }
    ]}
  ],

  /* Day by day. Each item: t = start hour (24h), kind = sight|ride|walk|train|flight|meal|free|stay,
     ref = sight id or leg id, from/to = points for rides (sight ids, or city.stay/hub/rail keys) */
  days: [
    { n: 0, city: "delhi", title: "Fly from Bangalore", items: [
      { t: 6.5, kind: "ride", from: "home", to: "homeAirport", label: "Uber to Kempegowda airport", cityRef: "blr" },
      { t: 9.5, kind: "flight", ref: "L0" },
      { t: 13.0, kind: "ride", from: "hub", to: "stay", label: "Uber T3 → Connaught Place" },
      { t: 18.0, kind: "sight", ref: "gate", label: "India Gate at dusk (preview)" },
      { t: 20.0, kind: "meal", label: "Dinner in Khan Market" }
    ]},
    { n: 1, city: "agra", title: "Agra: fort and the far bank", items: [
      { t: 7.0, kind: "ride", from: "stay", to: "rail", label: "Uber CP → Nizamuddin", cityRef: "delhi" },
      { t: 8.17, kind: "train", ref: "L1" },
      { t: 10.0, kind: "ride", from: "hub", to: "stay", label: "Uber Agra Cantt → Taj Ganj hotel" },
      { t: 12.0, kind: "sight", ref: "fort" },
      { t: 14.5, kind: "meal", label: "Lunch: petha and Mughlai at Pinch of Spice" },
      { t: 16.5, kind: "ride", from: "fort", to: "mehtab", label: "Auto to Mehtab Bagh" },
      { t: 17.0, kind: "sight", ref: "mehtab", label: "Mehtab Bagh for sunset" }
    ]},
    { n: 2, city: "agra", title: "Sunrise at the Taj, back to Delhi", items: [
      { t: 5.5, kind: "walk", label: "Walk to the East Gate (from Taj Ganj)" },
      { t: 6.0, kind: "sight", ref: "taj" },
      { t: 9.0, kind: "meal", label: "Late breakfast, rooftop with Taj view" },
      { t: 10.5, kind: "ride", from: "taj", to: "sikri", label: "Cab to Fatehpur Sikri (optional)" },
      { t: 11.5, kind: "sight", ref: "sikri" },
      { t: 15.0, kind: "ride", from: "sikri", to: "hub", label: "Cab back to Agra Cantt" },
      { t: 17.83, kind: "train", ref: "L2" },
      { t: 19.75, kind: "ride", from: "rail", to: "stay", label: "Uber Nizamuddin → CP", cityRef: "delhi" }
    ]},
    { n: 3, city: "delhi", title: "Old Delhi on foot", items: [
      { t: 9.0, kind: "ride", from: "stay", to: "redfort", label: "Metro to Lal Qila (Violet line)", metro: true },
      { t: 9.5, kind: "sight", ref: "redfort" },
      { t: 12.0, kind: "walk", label: "Walk to Jama Masjid through Meena Bazaar" },
      { t: 12.25, kind: "sight", ref: "jama" },
      { t: 13.5, kind: "sight", ref: "chowk", label: "Chandni Chowk: lunch in Paranthe Wali Gali" },
      { t: 16.0, kind: "ride", from: "chowk", to: "stay", label: "Metro back to Rajiv Chowk", metro: true },
      { t: 19.0, kind: "free", label: "Evening free: Connaught Place, Janpath" }
    ]},
    { n: 4, city: "delhi", title: "Tombs and towers", items: [
      { t: 8.5, kind: "ride", from: "stay", to: "humayun", label: "Uber to Humayun's Tomb" },
      { t: 9.0, kind: "sight", ref: "humayun" },
      { t: 11.0, kind: "ride", from: "humayun", to: "qutub", label: "Uber to Qutub Minar" },
      { t: 12.0, kind: "sight", ref: "qutub" },
      { t: 14.0, kind: "meal", label: "Lunch in Mehrauli / Champa Gali" },
      { t: 16.0, kind: "ride", from: "qutub", to: "stay", label: "Metro Qutub Minar → Rajiv Chowk (Yellow line)", metro: true }
    ]},
    { n: 5, city: "delhi", title: "Lotus, Lodhi, and a slow evening", items: [
      { t: 9.0, kind: "ride", from: "stay", to: "lotus", label: "Uber to Lotus Temple" },
      { t: 9.75, kind: "sight", ref: "lotus" },
      { t: 11.5, kind: "free", label: "Lodhi Garden and Lodhi Art District" },
      { t: 14.0, kind: "meal", label: "Lunch at Khan Market" },
      { t: 17.0, kind: "sight", ref: "gate", label: "India Gate, properly this time" },
      { t: 20.0, kind: "free", label: "Hauz Khas Village for the evening" }
    ]},
    { n: 6, city: "delhi", title: "Last morning in Delhi, fly east", items: [
      { t: 9.0, kind: "free", label: "Markets: Dilli Haat or Sarojini Nagar" },
      { t: 13.0, kind: "meal", label: "Lunch near the hotel; checkout" },
      { t: 14.5, kind: "ride", from: "stay", to: "hub", label: "Uber CP → T3 (allow buffer)" },
      { t: 17.5, kind: "flight", ref: "L3" },
      { t: 19.5, kind: "ride", from: "hub", to: "stay", label: "Prebooked cab airport → Assi Ghat", fixed: [580, 700], cityRef: "varanasi" }
    ]},
    { n: 7, city: "varanasi", title: "Along the river", items: [
      { t: 8.0, kind: "sight", ref: "ghats", label: "Walk the ghats, Assi to Dashashwamedh" },
      { t: 12.0, kind: "meal", label: "Kachori sabzi, then lassi in a clay cup" },
      { t: 14.0, kind: "free", label: "Rest through the heat; lanes of Bengali Tola" },
      { t: 17.0, kind: "walk", label: "Boat pickup at Assi Ghat" },
      { t: 18.0, kind: "sight", ref: "aarti", label: "Ganga Aarti from the water" }
    ]},
    { n: 8, city: "varanasi", title: "Dawn boat, temple, Sarnath", items: [
      { t: 5.5, kind: "sight", ref: "ghats", label: "Sunrise boat ride", short: true },
      { t: 8.0, kind: "walk", label: "Walk to the Vishwanath corridor" },
      { t: 8.5, kind: "sight", ref: "kashi" },
      { t: 11.0, kind: "ride", from: "kashi", to: "sarnath", label: "Cab to Sarnath" },
      { t: 12.0, kind: "sight", ref: "sarnath" },
      { t: 15.0, kind: "ride", from: "sarnath", to: "stay", label: "Cab back to Assi Ghat" },
      { t: 19.0, kind: "free", label: "Last evening on the steps" }
    ]},
    { n: 9, city: "varanasi", title: "Fly home", items: [
      { t: 7.5, kind: "meal", label: "Breakfast on the ghat" },
      { t: 8.5, kind: "ride", from: "stay", to: "hub", label: "Prebooked cab Assi → airport", fixed: [580, 700] },
      { t: 11.67, kind: "flight", ref: "L4" },
      { t: 14.5, kind: "ride", from: "homeAirport", to: "home", label: "Uber home from BLR", cityRef: "blr" }
    ]}
  ],

  budget: {
    hotels: [ { name: "Guesthouse", night: 2500 }, { name: "Boutique", night: 6000 }, { name: "Heritage / 5★", night: 15000 } ],
    food: [ { name: "Street & dhaba", day: 800 }, { name: "Mixed", day: 1500 }, { name: "Restaurants", day: 3000 } ],
    extras: [ { name: "Sunrise boat (shared)", pp: 300 }, { name: "Aarti boat (shared)", pp: 250 }, { name: "Guides & tips", pp: 1500 }, { name: "SIM / data", pp: 400 } ]
  },

  homeRide: { base: 60, perKm: 13, perMin: 1.4, min: 100, peak: 1.5, speeds: [40,40,40,40,40,36,28,20,16,16,20,24,26,26,26,24,20,16,14,16,22,30,36,40] },

  festivals: [
    { m: 2, name: "Taj Mahotsav (Agra, 10 days)" }, { m: 3, name: "Holi: Mathura & Vrindavan are 60 km from Agra" },
    { m: 10, name: "Dussehra & Diwali (dates shift; book early)" }, { m: 11, name: "Dev Deepawali: a million lamps on the ghats (Kartik Purnima)" },
    { m: 11, name: "Delhi stubble-burning smog peaks; GRAP curbs can hit diesel cabs and add traffic checks" },
    { m: 11, name: "Dev Deepawali falls on 24 Nov 2026, four days before you land: the ghats will still be dressed" }, { m: 1, name: "Republic Day parade on Kartavya Path, 26 Jan" }, { m: 12, name: "Dense fog can delay Delhi flights and trains" }
  ],

  packing: {
    base: ["Comfortable closed shoes (Taj shoe covers provided)", "Scarf for mosques and temples", "Power bank", "Copies of ID for monuments"],
    hot: ["Sun hat and SPF 50", "Electrolyte sachets", "Loose cotton"],
    cold: ["A real jacket for Delhi mornings", "Layers for the 05:30 boat"],
    wet: ["Compact umbrella", "Dry bag for the phone on the boat"],
    smog: ["N95 / FFP2 masks, two per person per city day", "Saline nasal spray and lubricating eye drops", "Ask hotels for rooms with air purifiers (most 4★+ in Delhi have them)", "Inhaler if you have ever needed one"]
  },

  sources: [
    ["Gatimaan Express fare & schedule", "https://blog.travelkhana.com/rail-info/12049-12050-gatimaan-express/"],
    ["Vande Bharat 22436 fare & schedule", "https://www.thequint.com/lifestyle/travel/vande-bharat-express-timing-routeticket-fare-22439-22440-22435-22436"],
    ["BLR–DEL flights", "https://www.ixigo.com/cheap-flights/bengaluru-new-delhi-blr-del"],
    ["DEL–VNS flights", "https://www.ixigo.com/cheap-flights/new-delhi-varanasi-del-vns"],
    ["VNS–BLR flights", "https://www.ixigo.com/cheap-flights/varanasi-bengaluru-vns-blr"],
    ["Delhi airport rides", "https://www.happyfares.in/blog/delhi-airport-guide-2026/"],
    ["Varanasi airport taxi", "https://www.kashitaxi.in/en/city/varanasi/taxi/varanasi-airport-to-dashashwamedh-distance"],
    ["Taj Mahal tickets 2026", "https://www.asiabylocals.com/india/agra/taj-mahal-ticket-price-2026"],
    ["Delhi monuments tickets", "https://tticketpricing.com/monuments/humayuns-tomb-delhi/"],
    ["Varanasi boat rides", "https://www.kashitaxi.in/en/evening-boat-ride-varanasi-ganga-aarti"],
    ["TomTom Traffic Index: New Delhi", "https://www.tomtom.com/traffic-index/city/new-delhi/"],
    ["Climate normals: Open-Meteo archive, 2023–2025 daily", "https://open-meteo.com/en/docs/historical-weather-api"],
    ["Live weather & AQI: Open-Meteo", "https://open-meteo.com/"],
    ["Delhi December 2025 AQI average 294", "https://www.deccanherald.com/india/delhi/delhi-records-best-december-aqi-since-system-began-in-2015-3336491"],
    ["CPCB city AQI trends 2015–2025", "https://tribe.t8np75rys.junction.express/uploads/2025/12-December/10-Wed/AQ-analysis-final_693962a3f2b57.pdf"],
    ["Hourly pollution pattern in winter", "https://smartairfilters.com/en/blog/what-time-of-day-is-air-pollution-lowest-in-india/"],
    ["Taj Mahal hidden by December fog", "https://www.aninews.in/news/national/general-news/dense-fog-engulfs-agra-taj-mahal-fades-from-view20251221083349/"]
  ]
};
