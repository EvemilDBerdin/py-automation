class CebuLocationBarangay:
    @classmethod
    def get_dynamic_location(cls, all_data):
        if not all_data['listing_description']:
            return "Cebu city, Cebu"

        cebu_cities = {
            "Cebu City": { 
                "barangays": [
                    "Adlaon", "Agsungot", "Apas", "Bacayan", "Banilad", "Basak Pardo",
                    "Basak San Nicolas", "Binaliw", "Bonbon", "Budlaan", "Buhisan",
                    "Bulacao", "Buot", "Busay", "Calamba", "Capitol Site", "Carreta",
                    "Cogon Pardo", "Cogon Ramos", "Day-as", "Duljo Fatima", "Ermita",
                    "Guadalupe", "Guba", "Hipodromo", "Inayawan", "Kalubihan",
                    "Kalunasan", "Kamagayan", "Kamputhaw", "Kasambagan", "Kinasang-an",
                    "Labangon", "Lahug", "Lorega", "Lusaran", "Luz", "Mabini",
                    "Mabolo", "Malubog", "Mambaling", "Pahina Central", "Pahina San Nicolas",
                    "Parian", "Paril", "Pasil", "Pit-os", "Poblacion Pardo",
                    "Pulangbato", "Pung-ol Sibugay", "Quiot", "Sambag I", "Sambag II",
                    "San Antonio", "San Jose", "San Nicolas Proper", "San Roque",
                    "Santa Cruz", "Santo Niño", "Sapangdaku", "Sawang Calero",
                    "Sirao", "Suba", "T. Padilla", "Tabunan", "Tagba-o", "Talamban",
                    "Taptap", "Tejero", "Tinago", "Tisa", "To-ong", "Zapatera"
                ]
            },
            "Mandaue City": { 
                "barangays": [
                    "Alang-alang", "Banilad", "Basak", "Cabancalan", "Cambaro",
                    "Canduman", "Casili", "Casuntingan", "Centro", "Cubacub",
                    "Guizo", "Ibabao-Estancia", "Labogon", "Looc", "Maguikay",
                    "Mantuyong", "Opao", "Pagsabungan", "Pakna-an", "Subangdaku",
                    "Tabok", "Tingub", "Tipolo", "Umapad"
                ]
            },
            "Lapu-Lapu City": { 
                "barangays": [
                    "Agus", "Babag", "Bankal", "Baring", "Basak", "Buaya",
                    "Canjulao", "Caubian", "Cawhagan", "Cordova", "Gunob",
                    "Ibo", "Looc", "Mactan", "Maribago", "Marigondon",
                    "Pajo", "Pajac", "Poblacion", "Punta Engaño", "Pusok",
                    "Sabang", "San Vicente", "Santa Rosa", "Subabasbas",
                    "Talima", "Tingo", "Tungasan"
                ]
            }, 
            "Bogo City": { 
                "barangays": [
                    "Anonang Norte", "Anonang Sur", "Banban", "Binabag",
                    "Bungtod", "Carbon", "Cayang", "Cogon", "Dakit",
                    "Don Pedro", "Gairan", "Guadalupe", "La Paz",
                    "Libertad", "Lourdes", "Malingin", "Nailon",
                    "Odlot", "Pandan", "Peaceland", "Polambato",
                    "Poblacion", "San Vicente", "Santo Niño",
                    "Santo Rosario", "Taytayan", "Tigcan", "Marangog",
                    "City Hall"
                ]
            },
            "Carcar City": { 
                "barangays": [
                    "Bolinawan", "Calidngan", "Can-asujan", "Guadalupe",
                    "Liburon", "Napo", "Ocaña", "Perrelos", "Poblacion I",
                    "Poblacion II", "Poblacion III", "Pob. Valencia",
                    "Pob. Valladolid", "Sab-ang", "Tuyom", "Valencia",
                    "Valladolid", "Can-irehan"
                ]
            },
            "Danao City": { 
                "barangays": [
                    "Bagakay", "Baliang", "Binaliw", "Cabungahan",
                    "Cahumayan", "Cambanay", "Cogon Cruz", "Cotcot",
                    "Danasan", "Daorong", "Dao", "Don Andres Soriano",
                    "Dunggoan", "Guinsay", "Gubagub", "Guinacot",
                    "Kanluhangon", "Langosig", "Lawaan", "Looc",
                    "Magtagobtob", "Mantija", "Masaba", "Maslog",
                    "Poblacion", "Sabang", "Sacsac", "Sandayong",
                    "Santa Rosa", "Tabok", "Taboc", "Tanke",
                    "Tawagan", "Togonon"
                ]
            },
            "Naga City": { 
                "barangays": [
                    "Alpaco", "Bairan", "Balirong", "Cantao-an",
                    "Central Poblacion", "Colon", "East Poblacion",
                    "Inoburan", "Inayagan", "Jaguimit", "Langtad",
                    "Lanas", "Lutac", "Mainit", "Mayana",
                    "North Poblacion", "Naalad", "Pangdan",
                    "South Poblacion", "West Poblacion", "Patag",
                    "Tangke", "Tinaan", "Tuyan", "Uling",
                    "West Tangke"
                ]
            },
            "Talisay City": { 
                "barangays": [
                    "Biasong", "Bulacao", "Cadulawan", "Camp 4",
                    "Cansojong", "Dumlog", "Jaclupan", "Lagtang",
                    "Lawaan I", "Lawaan II", "Lawaan III", "Linao",
                    "Maghaway", "Manipis", "Mohon", "Poblacion",
                    "Pooc", "San Isidro", "San Roque", "Tabunok",
                    "Tangke", "Tapul"
                ]
            },
            "Toledo City": { 
                "barangays": [
                    "Awihao", "Bagakay", "Bato", "Bunga", "Calongcalong",
                    "Cambang-ug", "Camp 8", "Cantabaco", "Capitan Claudio",
                    "Carmen", "Daanlungsod", "Don Andres Soriano",
                    "Dumlog", "Gen. Climaco", "Ilihan", "Juan Climaco",
                    "Landahan", "Luray II", "Lutopan", "Matab-ang",
                    "Media Once", "Poog", "Poblacion", "Putingbato",
                    "Sam-ang", "Sangi", "Santo Niño", "Tubod",
                    "Tungkop", "Pangamihan", "Canlumampao"
                ]
            }
        }
        try: 
            location_start = all_data['listing_description'].lower().find("location:") + len("Location:")
            location_end = all_data['listing_description'].find("\n", location_start)
            query_location = all_data['listing_description'][location_start:location_end].strip()
            query_location = query_location.lower().strip()
            
            result = {
                'city': "",
                'barangay': "",
                'original_query': query_location
            }
          
            # First try to identify the city
            for city_name in cebu_cities.keys():
                city_variations = [
                    city_name.lower(),
                    city_name.lower().replace(" city", ""),
                    city_name.lower().split()[0]  # For cases like "Lapu-Lapu"
                ]
                
                if any(variation in query_location for variation in city_variations):
                    result['city'] = city_name
                    
                    # Now search for barangay within this city
                    for barangay in cebu_cities[city_name]['barangays']:
                        # Create variations of barangay name
                        barangay_variations = [
                            barangay.lower(),
                            f"brgy. {barangay.lower()}",
                            f"barangay {barangay.lower()}",
                            f"brgy {barangay.lower()}",
                            f"{barangay.lower()} area",
                            barangay.lower().replace("-", " ")
                        ]
                        
                        # Additional check for Mactan special case
                        if 'mactan newtown' in query_location and city_name == 'Lapu-Lapu City':
                            result['barangay'] = 'Mactan'
                            return result
                            
                        # Check if any variation of the barangay is in the query
                        if any(variation in query_location for variation in barangay_variations):
                            result['barangay'] = barangay
                            return result
                    
                    # If we found a city but no barangay, we still return what we found
                    break

            # If no city was found yet, try searching all barangays
            if not result['city']:
                for city_name, city_data in cebu_cities.items():
                    for barangay in city_data['barangays']:
                        barangay_variations = [
                            barangay.lower(),
                            f"brgy. {barangay.lower()}",
                            f"barangay {barangay.lower()}",
                            f"brgy {barangay.lower()}",
                            f"{barangay.lower()} area",
                            barangay.lower().replace("-", " ")
                        ]
                        
                        if any(variation in query_location for variation in barangay_variations):
                            result['city'] = city_name
                            result['barangay'] = barangay
                            return result
            return result
        except Exception as e:
            print('error on location: ', e)
            return