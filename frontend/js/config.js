// Application Global Configuration — Professional Google Maps Navigation Edition
const CONFIG = {
  API_BASE_URL: window.location.origin + '/api',
  DEFAULT_CENTER: [22.8046, 86.2029], // Working default coordinates
  DEFAULT_ZOOM: 13,
  MAX_WAYPOINTS: 5,

  // Google Maps Platform Frontend Configuration
  GOOGLE_MAPS: {
    BROWSER_KEY: '',
    IS_ENABLED: false
  },

  // 100% Free & Open-Source OpenStreetMap Tile Layer (Zero API Key Required)
  MAP_TILES: {
    OSM_URL: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    ATTRIBUTION: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap contributors</a>',
    MAX_ZOOM: 19
  },

  // Google Maps Classic Palette
  COLORS: {
    GOOGLE_BLUE: '#1a73e8',
    GOOGLE_BLUE_HOVER: '#1557b0',
    GOOGLE_GREEN: '#188038',
    GOOGLE_YELLOW: '#f29900',
    GOOGLE_RED: '#d93025',
    GOOGLE_GREY: '#70757a',
    GOOGLE_LIGHT_GREY: '#f1f3f4',
    GOOGLE_BORDER: '#dadce0',
    TEXT_MAIN: '#202124',
    TEXT_MUTED: '#5f6368'
  },

  ROUTE_COLORS: {
    PRIMARY: '#1a73e8',       // Crisp Google Blue
    PRIMARY_CASING: '#ffffff',
    ALTERNATIVE: '#70757a',   // Google Muted Slate Grey
    BLOCKED: '#d93025',       // Hazard Warning Red
    WALKING: '#188038',       // Google Pedestrian Green
    BICYCLE: '#1a73e8'        // Google Cycling Blue
  },

  // Points of Interest Categories from Overpass API
  POI_CATEGORIES: {
    restaurant: { label: 'Restaurants', icon: 'utensils', color: '#e37400', bg: '#fef7e0', tag: 'Food' },
    hotel: { label: 'Hotels', icon: 'bed', color: '#1a73e8', bg: '#e8f0fe', tag: 'Stays' },
    hospital: { label: 'Hospitals', icon: 'heart-pulse', color: '#d93025', bg: '#fce8e6', tag: 'Health' },
    pharmacy: { label: 'Pharmacies', icon: 'cross', color: '#188038', bg: '#e6f4ea', tag: 'Pharma' },
    petrol: { label: 'Petrol Pumps', icon: 'fuel', color: '#8430ce', bg: '#f3e8fd', tag: 'Fuel' },
    atm: { label: 'ATMs & Banks', icon: 'credit-card', color: '#129eaf', bg: '#e4f7fb', tag: 'Finance' },
    mall: { label: 'Malls & Shops', icon: 'shopping-bag', color: '#d01884', bg: '#fde7f3', tag: 'Shopping' },
    school: { label: 'Schools', icon: 'book-open', color: '#137333', bg: '#e6f4ea', tag: 'Education' },
    college: { label: 'Colleges', icon: 'graduation-cap', color: '#1a73e8', bg: '#e8f0fe', tag: 'Higher Ed' },
    railway: { label: 'Train Stations', icon: 'train', color: '#e37400', bg: '#fef7e0', tag: 'Transit' },
    bus_stop: { label: 'Bus Stops', icon: 'bus', color: '#5f6368', bg: '#f1f3f4', tag: 'Transit' }
  }
};
