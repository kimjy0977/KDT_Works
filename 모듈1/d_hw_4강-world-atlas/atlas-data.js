// 자동 생성(enrich.mjs) — mledoze/countries + World Bank. 수정 금지, 재생성으로 갱신.
const ATLAS_META = {
 "ae": {
  "iso2": "AE",
  "iso3": "ARE",
  "region": "Asia",
  "subregion": "Western Asia",
  "demonym": "Emirati",
  "landlocked": false,
  "latlng": [
   24,
   54
  ],
  "area": 83600,
  "neighbors": [
   {
    "code": "om",
    "name": "Oman",
    "inAtlas": false
   },
   {
    "code": "sa",
    "name": "Saudi Arabia",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": null,
   "gdppc": null,
   "lifeExp": 83.1,
   "urban": 86,
   "year": null
  }
 },
 "ar": {
  "iso2": "AR",
  "iso3": "ARG",
  "region": "Americas",
  "subregion": "South America",
  "demonym": "Argentine",
  "landlocked": false,
  "latlng": [
   -34,
   -64
  ],
  "area": 2780400,
  "neighbors": [
   {
    "code": "bo",
    "name": "Bolivia",
    "inAtlas": false
   },
   {
    "code": "br",
    "name": "Brazil",
    "inAtlas": true
   },
   {
    "code": "cl",
    "name": "Chile",
    "inAtlas": true
   },
   {
    "code": "py",
    "name": "Paraguay",
    "inAtlas": false
   },
   {
    "code": "uy",
    "name": "Uruguay",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 683097891619,
   "gdppc": 14898,
   "lifeExp": 77.5,
   "urban": 92.4,
   "year": "2025"
  }
 },
 "au": {
  "iso2": "AU",
  "iso3": "AUS",
  "region": "Oceania",
  "subregion": "Australia and New Zealand",
  "demonym": "Australian",
  "landlocked": false,
  "latlng": [
   -27,
   133
  ],
  "area": 7692024,
  "neighbors": [],
  "econ": {
   "gdp": 1798518933689,
   "gdppc": 65130,
   "lifeExp": 83.1,
   "urban": 87.7,
   "year": "2025"
  }
 },
 "br": {
  "iso2": "BR",
  "iso3": "BRA",
  "region": "Americas",
  "subregion": "South America",
  "demonym": "Brazilian",
  "landlocked": false,
  "latlng": [
   -10,
   -55
  ],
  "area": 8515767,
  "neighbors": [
   {
    "code": "ar",
    "name": "Argentina",
    "inAtlas": true
   },
   {
    "code": "bo",
    "name": "Bolivia",
    "inAtlas": false
   },
   {
    "code": "co",
    "name": "Colombia",
    "inAtlas": true
   },
   {
    "code": "gf",
    "name": "French Guiana",
    "inAtlas": false
   },
   {
    "code": "gy",
    "name": "Guyana",
    "inAtlas": false
   },
   {
    "code": "py",
    "name": "Paraguay",
    "inAtlas": false
   },
   {
    "code": "pe",
    "name": "Peru",
    "inAtlas": true
   },
   {
    "code": "sr",
    "name": "Suriname",
    "inAtlas": false
   },
   {
    "code": "uy",
    "name": "Uruguay",
    "inAtlas": false
   },
   {
    "code": "ve",
    "name": "Venezuela",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 2279920092492,
   "gdppc": 10713,
   "lifeExp": 76,
   "urban": 88.2,
   "year": "2025"
  }
 },
 "ca": {
  "iso2": "CA",
  "iso3": "CAN",
  "region": "Americas",
  "subregion": "North America",
  "demonym": "Canadian",
  "landlocked": false,
  "latlng": [
   60,
   -95
  ],
  "area": 9984670,
  "neighbors": [
   {
    "code": "us",
    "name": "United States",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": 2319899772426,
   "gdppc": 55698,
   "lifeExp": 82.1,
   "urban": 82.9,
   "year": "2025"
  }
 },
 "ch": {
  "iso2": "CH",
  "iso3": "CHE",
  "region": "Europe",
  "subregion": "Western Europe",
  "demonym": "Swiss",
  "landlocked": true,
  "latlng": [
   47,
   8
  ],
  "area": 41284,
  "neighbors": [
   {
    "code": "at",
    "name": "Austria",
    "inAtlas": false
   },
   {
    "code": "fr",
    "name": "France",
    "inAtlas": true
   },
   {
    "code": "it",
    "name": "Italy",
    "inAtlas": true
   },
   {
    "code": "li",
    "name": "Liechtenstein",
    "inAtlas": false
   },
   {
    "code": "de",
    "name": "Germany",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": 1043529899251,
   "gdppc": 114769,
   "lifeExp": 84.4,
   "urban": 85.7,
   "year": "2025"
  }
 },
 "cl": {
  "iso2": "CL",
  "iso3": "CHL",
  "region": "Americas",
  "subregion": "South America",
  "demonym": "Chilean",
  "landlocked": false,
  "latlng": [
   -30,
   -71
  ],
  "area": 756102,
  "neighbors": [
   {
    "code": "ar",
    "name": "Argentina",
    "inAtlas": true
   },
   {
    "code": "bo",
    "name": "Bolivia",
    "inAtlas": false
   },
   {
    "code": "pe",
    "name": "Peru",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": 357371159575,
   "gdppc": 17995,
   "lifeExp": 81.4,
   "urban": 89.2,
   "year": "2025"
  }
 },
 "cn": {
  "iso2": "CN",
  "iso3": "CHN",
  "region": "Asia",
  "subregion": "Eastern Asia",
  "demonym": "Chinese",
  "landlocked": false,
  "latlng": [
   35,
   105
  ],
  "area": 9706961,
  "neighbors": [
   {
    "code": "af",
    "name": "Afghanistan",
    "inAtlas": false
   },
   {
    "code": "bt",
    "name": "Bhutan",
    "inAtlas": false
   },
   {
    "code": "mm",
    "name": "Myanmar",
    "inAtlas": false
   },
   {
    "code": "hk",
    "name": "Hong Kong",
    "inAtlas": false
   },
   {
    "code": "in",
    "name": "India",
    "inAtlas": true
   },
   {
    "code": "kz",
    "name": "Kazakhstan",
    "inAtlas": false
   },
   {
    "code": "np",
    "name": "Nepal",
    "inAtlas": false
   },
   {
    "code": "kp",
    "name": "North Korea",
    "inAtlas": false
   },
   {
    "code": "kg",
    "name": "Kyrgyzstan",
    "inAtlas": false
   },
   {
    "code": "la",
    "name": "Laos",
    "inAtlas": false
   },
   {
    "code": "mo",
    "name": "Macau",
    "inAtlas": false
   },
   {
    "code": "mn",
    "name": "Mongolia",
    "inAtlas": false
   },
   {
    "code": "pk",
    "name": "Pakistan",
    "inAtlas": false
   },
   {
    "code": "ru",
    "name": "Russia",
    "inAtlas": true
   },
   {
    "code": "tj",
    "name": "Tajikistan",
    "inAtlas": false
   },
   {
    "code": "vn",
    "name": "Vietnam",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": 19498039388043,
   "gdppc": 13862,
   "lifeExp": 78,
   "urban": 66.3,
   "year": "2025"
  }
 },
 "co": {
  "iso2": "CO",
  "iso3": "COL",
  "region": "Americas",
  "subregion": "South America",
  "demonym": "Colombian",
  "landlocked": false,
  "latlng": [
   4,
   -72
  ],
  "area": 1141748,
  "neighbors": [
   {
    "code": "br",
    "name": "Brazil",
    "inAtlas": true
   },
   {
    "code": "ec",
    "name": "Ecuador",
    "inAtlas": false
   },
   {
    "code": "pa",
    "name": "Panama",
    "inAtlas": false
   },
   {
    "code": "pe",
    "name": "Peru",
    "inAtlas": true
   },
   {
    "code": "ve",
    "name": "Venezuela",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 457410034203,
   "gdppc": 8562,
   "lifeExp": 77.9,
   "urban": 78.8,
   "year": "2025"
  }
 },
 "de": {
  "iso2": "DE",
  "iso3": "DEU",
  "region": "Europe",
  "subregion": "Western Europe",
  "demonym": "German",
  "landlocked": false,
  "latlng": [
   51,
   9
  ],
  "area": 357114,
  "neighbors": [
   {
    "code": "at",
    "name": "Austria",
    "inAtlas": false
   },
   {
    "code": "be",
    "name": "Belgium",
    "inAtlas": false
   },
   {
    "code": "cz",
    "name": "Czechia",
    "inAtlas": false
   },
   {
    "code": "dk",
    "name": "Denmark",
    "inAtlas": false
   },
   {
    "code": "fr",
    "name": "France",
    "inAtlas": true
   },
   {
    "code": "lu",
    "name": "Luxembourg",
    "inAtlas": false
   },
   {
    "code": "nl",
    "name": "Netherlands",
    "inAtlas": true
   },
   {
    "code": "pl",
    "name": "Poland",
    "inAtlas": false
   },
   {
    "code": "ch",
    "name": "Switzerland",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": 5050922925047,
   "gdppc": 60496,
   "lifeExp": 80.8,
   "urban": 82.1,
   "year": "2025"
  }
 },
 "eg": {
  "iso2": "EG",
  "iso3": "EGY",
  "region": "Africa",
  "subregion": "Northern Africa",
  "demonym": "Egyptian",
  "landlocked": false,
  "latlng": [
   27,
   30
  ],
  "area": 1002450,
  "neighbors": [
   {
    "code": "il",
    "name": "Israel",
    "inAtlas": false
   },
   {
    "code": "ly",
    "name": "Libya",
    "inAtlas": false
   },
   {
    "code": "ps",
    "name": "Palestine",
    "inAtlas": false
   },
   {
    "code": "sd",
    "name": "Sudan",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 365254630180,
   "gdppc": 3086,
   "lifeExp": 71.8,
   "urban": 42.9,
   "year": "2025"
  }
 },
 "es": {
  "iso2": "ES",
  "iso3": "ESP",
  "region": "Europe",
  "subregion": "Southern Europe",
  "demonym": "Spanish",
  "landlocked": false,
  "latlng": [
   40,
   -4
  ],
  "area": 505992,
  "neighbors": [
   {
    "code": "ad",
    "name": "Andorra",
    "inAtlas": false
   },
   {
    "code": "fr",
    "name": "France",
    "inAtlas": true
   },
   {
    "code": "gi",
    "name": "Gibraltar",
    "inAtlas": false
   },
   {
    "code": "pt",
    "name": "Portugal",
    "inAtlas": true
   },
   {
    "code": "ma",
    "name": "Morocco",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": 1906453309986,
   "gdppc": 38627,
   "lifeExp": 83.9,
   "urban": 80.5,
   "year": "2025"
  }
 },
 "fr": {
  "iso2": "FR",
  "iso3": "FRA",
  "region": "Europe",
  "subregion": "Western Europe",
  "demonym": "French",
  "landlocked": false,
  "latlng": [
   46,
   2
  ],
  "area": 551695,
  "neighbors": [
   {
    "code": "ad",
    "name": "Andorra",
    "inAtlas": false
   },
   {
    "code": "be",
    "name": "Belgium",
    "inAtlas": false
   },
   {
    "code": "de",
    "name": "Germany",
    "inAtlas": true
   },
   {
    "code": "it",
    "name": "Italy",
    "inAtlas": true
   },
   {
    "code": "lu",
    "name": "Luxembourg",
    "inAtlas": false
   },
   {
    "code": "mc",
    "name": "Monaco",
    "inAtlas": false
   },
   {
    "code": "es",
    "name": "Spain",
    "inAtlas": true
   },
   {
    "code": "ch",
    "name": "Switzerland",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": 3366315927447,
   "gdppc": 48986,
   "lifeExp": 83,
   "urban": 78.8,
   "year": "2025"
  }
 },
 "gb": {
  "iso2": "GB",
  "iso3": "GBR",
  "region": "Europe",
  "subregion": "Northern Europe",
  "demonym": "British",
  "landlocked": false,
  "latlng": [
   54,
   -2
  ],
  "area": 242900,
  "neighbors": [
   {
    "code": "ie",
    "name": "Ireland",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 4002587541846,
   "gdppc": 57602,
   "lifeExp": 81.4,
   "urban": 83.3,
   "year": "2025"
  }
 },
 "gr": {
  "iso2": "GR",
  "iso3": "GRC",
  "region": "Europe",
  "subregion": "Southern Europe",
  "demonym": "Greek",
  "landlocked": false,
  "latlng": [
   39,
   22
  ],
  "area": 131990,
  "neighbors": [
   {
    "code": "al",
    "name": "Albania",
    "inAtlas": false
   },
   {
    "code": "bg",
    "name": "Bulgaria",
    "inAtlas": false
   },
   {
    "code": "tr",
    "name": "Türkiye",
    "inAtlas": true
   },
   {
    "code": "mk",
    "name": "North Macedonia",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 280635521324,
   "gdppc": 26948,
   "lifeExp": 81.8,
   "urban": 79.2,
   "year": "2025"
  }
 },
 "id": {
  "iso2": "ID",
  "iso3": "IDN",
  "region": "Asia",
  "subregion": "South-Eastern Asia",
  "demonym": "Indonesian",
  "landlocked": false,
  "latlng": [
   -5,
   120
  ],
  "area": 1904569,
  "neighbors": [
   {
    "code": "tl",
    "name": "Timor-Leste",
    "inAtlas": false
   },
   {
    "code": "my",
    "name": "Malaysia",
    "inAtlas": false
   },
   {
    "code": "pg",
    "name": "Papua New Guinea",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 1445642584164,
   "gdppc": 5060,
   "lifeExp": 71.3,
   "urban": 59.4,
   "year": "2025"
  }
 },
 "in": {
  "iso2": "IN",
  "iso3": "IND",
  "region": "Asia",
  "subregion": "Southern Asia",
  "demonym": "Indian",
  "landlocked": false,
  "latlng": [
   20,
   77
  ],
  "area": 3287590,
  "neighbors": [
   {
    "code": "bd",
    "name": "Bangladesh",
    "inAtlas": false
   },
   {
    "code": "bt",
    "name": "Bhutan",
    "inAtlas": false
   },
   {
    "code": "mm",
    "name": "Myanmar",
    "inAtlas": false
   },
   {
    "code": "cn",
    "name": "China",
    "inAtlas": true
   },
   {
    "code": "np",
    "name": "Nepal",
    "inAtlas": false
   },
   {
    "code": "pk",
    "name": "Pakistan",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 3956067115772,
   "gdppc": 2702,
   "lifeExp": 72.2,
   "urban": 35.7,
   "year": "2025"
  }
 },
 "it": {
  "iso2": "IT",
  "iso3": "ITA",
  "region": "Europe",
  "subregion": "Southern Europe",
  "demonym": "Italian",
  "landlocked": false,
  "latlng": [
   42.83333333,
   12.83333333
  ],
  "area": 301336,
  "neighbors": [
   {
    "code": "at",
    "name": "Austria",
    "inAtlas": false
   },
   {
    "code": "fr",
    "name": "France",
    "inAtlas": true
   },
   {
    "code": "sm",
    "name": "San Marino",
    "inAtlas": false
   },
   {
    "code": "si",
    "name": "Slovenia",
    "inAtlas": false
   },
   {
    "code": "ch",
    "name": "Switzerland",
    "inAtlas": true
   },
   {
    "code": "va",
    "name": "Vatican City",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": 2551556954100,
   "gdppc": 43309,
   "lifeExp": 84,
   "urban": 69.7,
   "year": "2025"
  }
 },
 "jp": {
  "iso2": "JP",
  "iso3": "JPN",
  "region": "Asia",
  "subregion": "Eastern Asia",
  "demonym": "Japanese",
  "landlocked": false,
  "latlng": [
   36,
   138
  ],
  "area": 377930,
  "neighbors": [],
  "econ": {
   "gdp": 4435162999977,
   "gdppc": 35951,
   "lifeExp": 84,
   "urban": 92.3,
   "year": "2025"
  }
 },
 "ke": {
  "iso2": "KE",
  "iso3": "KEN",
  "region": "Africa",
  "subregion": "Eastern Africa",
  "demonym": "Kenyan",
  "landlocked": false,
  "latlng": [
   1,
   38
  ],
  "area": 580367,
  "neighbors": [
   {
    "code": "et",
    "name": "Ethiopia",
    "inAtlas": false
   },
   {
    "code": "so",
    "name": "Somalia",
    "inAtlas": false
   },
   {
    "code": "ss",
    "name": "South Sudan",
    "inAtlas": false
   },
   {
    "code": "tz",
    "name": "Tanzania",
    "inAtlas": false
   },
   {
    "code": "ug",
    "name": "Uganda",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 135941278879,
   "gdppc": 2363,
   "lifeExp": 63.8,
   "urban": 32.2,
   "year": "2025"
  }
 },
 "kr": {
  "iso2": "KR",
  "iso3": "KOR",
  "region": "Asia",
  "subregion": "Eastern Asia",
  "demonym": "South Korean",
  "landlocked": false,
  "latlng": [
   37,
   127.5
  ],
  "area": 100210,
  "neighbors": [
   {
    "code": "kp",
    "name": "North Korea",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 1872374961553,
   "gdppc": 36227,
   "lifeExp": 83.6,
   "urban": 81.2,
   "year": "2025"
  }
 },
 "ma": {
  "iso2": "MA",
  "iso3": "MAR",
  "region": "Africa",
  "subregion": "Northern Africa",
  "demonym": "Moroccan",
  "landlocked": false,
  "latlng": [
   32,
   -5
  ],
  "area": 446550,
  "neighbors": [
   {
    "code": "dz",
    "name": "Algeria",
    "inAtlas": false
   },
   {
    "code": "eh",
    "name": "Western Sahara",
    "inAtlas": false
   },
   {
    "code": "es",
    "name": "Spain",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": 182374250612,
   "gdppc": 4672,
   "lifeExp": 75.5,
   "urban": 63.1,
   "year": "2025"
  }
 },
 "mx": {
  "iso2": "MX",
  "iso3": "MEX",
  "region": "Americas",
  "subregion": "North America",
  "demonym": "Mexican",
  "landlocked": false,
  "latlng": [
   23,
   -102
  ],
  "area": 1964375,
  "neighbors": [
   {
    "code": "bz",
    "name": "Belize",
    "inAtlas": false
   },
   {
    "code": "gt",
    "name": "Guatemala",
    "inAtlas": false
   },
   {
    "code": "us",
    "name": "United States",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": 1832641364776,
   "gdppc": 13889,
   "lifeExp": 75.3,
   "urban": 80,
   "year": "2025"
  }
 },
 "ng": {
  "iso2": "NG",
  "iso3": "NGA",
  "region": "Africa",
  "subregion": "Western Africa",
  "demonym": "Nigerian",
  "landlocked": false,
  "latlng": [
   10,
   8
  ],
  "area": 923768,
  "neighbors": [
   {
    "code": "bj",
    "name": "Benin",
    "inAtlas": false
   },
   {
    "code": "cm",
    "name": "Cameroon",
    "inAtlas": false
   },
   {
    "code": "td",
    "name": "Chad",
    "inAtlas": false
   },
   {
    "code": "ne",
    "name": "Niger",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 290794361542,
   "gdppc": 1224,
   "lifeExp": 54.6,
   "urban": 63.8,
   "year": "2025"
  }
 },
 "nl": {
  "iso2": "NL",
  "iso3": "NLD",
  "region": "Europe",
  "subregion": "Western Europe",
  "demonym": "Dutch",
  "landlocked": false,
  "latlng": [
   52.5,
   5.75
  ],
  "area": 41850,
  "neighbors": [
   {
    "code": "be",
    "name": "Belgium",
    "inAtlas": false
   },
   {
    "code": "de",
    "name": "Germany",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": 1332767651100,
   "gdppc": 73684,
   "lifeExp": 82,
   "urban": 95.9,
   "year": "2025"
  }
 },
 "no": {
  "iso2": "NO",
  "iso3": "NOR",
  "region": "Europe",
  "subregion": "Northern Europe",
  "demonym": "Norwegian",
  "landlocked": false,
  "latlng": [
   62,
   10
  ],
  "area": 323802,
  "neighbors": [
   {
    "code": "fi",
    "name": "Finland",
    "inAtlas": false
   },
   {
    "code": "se",
    "name": "Sweden",
    "inAtlas": true
   },
   {
    "code": "ru",
    "name": "Russia",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": 530755719439,
   "gdppc": 94594,
   "lifeExp": 83.2,
   "urban": 83.6,
   "year": "2025"
  }
 },
 "nz": {
  "iso2": "NZ",
  "iso3": "NZL",
  "region": "Oceania",
  "subregion": "Australia and New Zealand",
  "demonym": "New Zealander",
  "landlocked": false,
  "latlng": [
   -41,
   174
  ],
  "area": 270467,
  "neighbors": [],
  "econ": {
   "gdp": 264057413740,
   "gdppc": 49591,
   "lifeExp": 82,
   "urban": 84,
   "year": "2025"
  }
 },
 "pe": {
  "iso2": "PE",
  "iso3": "PER",
  "region": "Americas",
  "subregion": "South America",
  "demonym": "Peruvian",
  "landlocked": false,
  "latlng": [
   -10,
   -76
  ],
  "area": 1285216,
  "neighbors": [
   {
    "code": "bo",
    "name": "Bolivia",
    "inAtlas": false
   },
   {
    "code": "br",
    "name": "Brazil",
    "inAtlas": true
   },
   {
    "code": "cl",
    "name": "Chile",
    "inAtlas": true
   },
   {
    "code": "co",
    "name": "Colombia",
    "inAtlas": true
   },
   {
    "code": "ec",
    "name": "Ecuador",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 334854659182,
   "gdppc": 9684,
   "lifeExp": 77.9,
   "urban": 85.6,
   "year": "2025"
  }
 },
 "ph": {
  "iso2": "PH",
  "iso3": "PHL",
  "region": "Asia",
  "subregion": "South-Eastern Asia",
  "demonym": "Filipino",
  "landlocked": false,
  "latlng": [
   13,
   122
  ],
  "area": 342353,
  "neighbors": [],
  "econ": {
   "gdp": 487086123720,
   "gdppc": 4171,
   "lifeExp": 69.9,
   "urban": 55.8,
   "year": "2025"
  }
 },
 "pt": {
  "iso2": "PT",
  "iso3": "PRT",
  "region": "Europe",
  "subregion": "Southern Europe",
  "demonym": "Portuguese",
  "landlocked": false,
  "latlng": [
   39.5,
   -8
  ],
  "area": 92090,
  "neighbors": [
   {
    "code": "es",
    "name": "Spain",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": 346639825142,
   "gdppc": 32082,
   "lifeExp": 82.4,
   "urban": 61.5,
   "year": "2025"
  }
 },
 "ru": {
  "iso2": "RU",
  "iso3": "RUS",
  "region": "Europe",
  "subregion": "Eastern Europe",
  "demonym": "Russian",
  "landlocked": false,
  "latlng": [
   60,
   100
  ],
  "area": 17098242,
  "neighbors": [
   {
    "code": "az",
    "name": "Azerbaijan",
    "inAtlas": false
   },
   {
    "code": "by",
    "name": "Belarus",
    "inAtlas": false
   },
   {
    "code": "cn",
    "name": "China",
    "inAtlas": true
   },
   {
    "code": "ee",
    "name": "Estonia",
    "inAtlas": false
   },
   {
    "code": "fi",
    "name": "Finland",
    "inAtlas": false
   },
   {
    "code": "ge",
    "name": "Georgia",
    "inAtlas": false
   },
   {
    "code": "kz",
    "name": "Kazakhstan",
    "inAtlas": false
   },
   {
    "code": "kp",
    "name": "North Korea",
    "inAtlas": false
   },
   {
    "code": "lv",
    "name": "Latvia",
    "inAtlas": false
   },
   {
    "code": "lt",
    "name": "Lithuania",
    "inAtlas": false
   },
   {
    "code": "mn",
    "name": "Mongolia",
    "inAtlas": false
   },
   {
    "code": "no",
    "name": "Norway",
    "inAtlas": true
   },
   {
    "code": "pl",
    "name": "Poland",
    "inAtlas": false
   },
   {
    "code": "ua",
    "name": "Ukraine",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 2561310169359,
   "gdppc": 17547,
   "lifeExp": 73.4,
   "urban": 75.3,
   "year": "2025"
  }
 },
 "sa": {
  "iso2": "SA",
  "iso3": "SAU",
  "region": "Asia",
  "subregion": "Western Asia",
  "demonym": "Saudi Arabian",
  "landlocked": false,
  "latlng": [
   25,
   45
  ],
  "area": 2149690,
  "neighbors": [
   {
    "code": "iq",
    "name": "Iraq",
    "inAtlas": false
   },
   {
    "code": "jo",
    "name": "Jordan",
    "inAtlas": false
   },
   {
    "code": "kw",
    "name": "Kuwait",
    "inAtlas": false
   },
   {
    "code": "om",
    "name": "Oman",
    "inAtlas": false
   },
   {
    "code": "qa",
    "name": "Qatar",
    "inAtlas": false
   },
   {
    "code": "ae",
    "name": "United Arab Emirates",
    "inAtlas": true
   },
   {
    "code": "ye",
    "name": "Yemen",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 1276942933333,
   "gdppc": 34537,
   "lifeExp": 79,
   "urban": 84.6,
   "year": "2025"
  }
 },
 "se": {
  "iso2": "SE",
  "iso3": "SWE",
  "region": "Europe",
  "subregion": "Northern Europe",
  "demonym": "Swedish",
  "landlocked": false,
  "latlng": [
   62,
   15
  ],
  "area": 450295,
  "neighbors": [
   {
    "code": "fi",
    "name": "Finland",
    "inAtlas": false
   },
   {
    "code": "no",
    "name": "Norway",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": 668998664082,
   "gdppc": 63133,
   "lifeExp": 84.1,
   "urban": 89.1,
   "year": "2025"
  }
 },
 "sg": {
  "iso2": "SG",
  "iso3": "SGP",
  "region": "Asia",
  "subregion": "South-Eastern Asia",
  "demonym": "Singaporean",
  "landlocked": false,
  "latlng": [
   1.36666666,
   103.8
  ],
  "area": 710,
  "neighbors": [],
  "econ": {
   "gdp": 603869516999,
   "gdppc": 98814,
   "lifeExp": 83.3,
   "urban": 100,
   "year": "2025"
  }
 },
 "th": {
  "iso2": "TH",
  "iso3": "THA",
  "region": "Asia",
  "subregion": "South-Eastern Asia",
  "demonym": "Thai",
  "landlocked": false,
  "latlng": [
   15,
   100
  ],
  "area": 513120,
  "neighbors": [
   {
    "code": "mm",
    "name": "Myanmar",
    "inAtlas": false
   },
   {
    "code": "kh",
    "name": "Cambodia",
    "inAtlas": false
   },
   {
    "code": "la",
    "name": "Laos",
    "inAtlas": false
   },
   {
    "code": "my",
    "name": "Malaysia",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 577009981112,
   "gdppc": 8057,
   "lifeExp": 76.6,
   "urban": 62.8,
   "year": "2025"
  }
 },
 "tr": {
  "iso2": "TR",
  "iso3": "TUR",
  "region": "Asia",
  "subregion": "Western Asia",
  "demonym": "Turkish",
  "landlocked": false,
  "latlng": [
   39,
   35
  ],
  "area": 783562,
  "neighbors": [
   {
    "code": "am",
    "name": "Armenia",
    "inAtlas": false
   },
   {
    "code": "az",
    "name": "Azerbaijan",
    "inAtlas": false
   },
   {
    "code": "bg",
    "name": "Bulgaria",
    "inAtlas": false
   },
   {
    "code": "ge",
    "name": "Georgia",
    "inAtlas": false
   },
   {
    "code": "gr",
    "name": "Greece",
    "inAtlas": true
   },
   {
    "code": "ir",
    "name": "Iran",
    "inAtlas": false
   },
   {
    "code": "iq",
    "name": "Iraq",
    "inAtlas": false
   },
   {
    "code": "sy",
    "name": "Syria",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 1597293229287,
   "gdppc": 18599,
   "lifeExp": 77.4,
   "urban": 89.5,
   "year": "2025"
  }
 },
 "us": {
  "iso2": "US",
  "iso3": "USA",
  "region": "Americas",
  "subregion": "North America",
  "demonym": "American",
  "landlocked": false,
  "latlng": [
   38,
   -97
  ],
  "area": 9372610,
  "neighbors": [
   {
    "code": "ca",
    "name": "Canada",
    "inAtlas": true
   },
   {
    "code": "mx",
    "name": "Mexico",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": 30769700000000,
   "gdppc": 90027,
   "lifeExp": 78.9,
   "urban": 80.2,
   "year": "2025"
  }
 },
 "va": {
  "iso2": "VA",
  "iso3": "VAT",
  "region": "Europe",
  "subregion": "Southern Europe",
  "demonym": "Vatican",
  "landlocked": true,
  "latlng": [
   41.9,
   12.45
  ],
  "area": 0.44,
  "neighbors": [
   {
    "code": "it",
    "name": "Italy",
    "inAtlas": true
   }
  ],
  "econ": {
   "gdp": null,
   "gdppc": null,
   "lifeExp": null,
   "urban": null,
   "year": null
  }
 },
 "vn": {
  "iso2": "VN",
  "iso3": "VNM",
  "region": "Asia",
  "subregion": "South-Eastern Asia",
  "demonym": "Vietnamese",
  "landlocked": false,
  "latlng": [
   16.16666666,
   107.83333333
  ],
  "area": 331212,
  "neighbors": [
   {
    "code": "kh",
    "name": "Cambodia",
    "inAtlas": false
   },
   {
    "code": "cn",
    "name": "China",
    "inAtlas": true
   },
   {
    "code": "la",
    "name": "Laos",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 514697215165,
   "gdppc": 5066,
   "lifeExp": 74.7,
   "urban": 38.8,
   "year": "2025"
  }
 },
 "za": {
  "iso2": "ZA",
  "iso3": "ZAF",
  "region": "Africa",
  "subregion": "Southern Africa",
  "demonym": "South African",
  "landlocked": false,
  "latlng": [
   -29,
   24
  ],
  "area": 1221037,
  "neighbors": [
   {
    "code": "bw",
    "name": "Botswana",
    "inAtlas": false
   },
   {
    "code": "ls",
    "name": "Lesotho",
    "inAtlas": false
   },
   {
    "code": "mz",
    "name": "Mozambique",
    "inAtlas": false
   },
   {
    "code": "na",
    "name": "Namibia",
    "inAtlas": false
   },
   {
    "code": "sz",
    "name": "Eswatini",
    "inAtlas": false
   },
   {
    "code": "zw",
    "name": "Zimbabwe",
    "inAtlas": false
   }
  ],
  "econ": {
   "gdp": 427184325997,
   "gdppc": 6598,
   "lifeExp": 66.3,
   "urban": 63.8,
   "year": "2025"
  }
 }
};
