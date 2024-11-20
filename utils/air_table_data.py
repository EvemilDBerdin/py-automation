import re
from pyairtable import Api

class AirtableDataHelper:
    API_KEY = 'test api key'
    BASE_ID = 'test base id'
    TABLE_ID = 'test table id'
    VIEW_TABLE = 'All'

    @staticmethod
    def get_table():
        api = Api(AirtableDataHelper.API_KEY)
        return api.table(AirtableDataHelper.BASE_ID, AirtableDataHelper.TABLE_ID)

    @staticmethod
    def extract_property_id(listing_description):
        if not isinstance(listing_description, str):
            return None
        match = re.search(r'Property ID: (\w+)', listing_description)
        return match.group(1) if match else None

    @staticmethod
    def get_airtable_record(propertyID = None):
        if not propertyID:
            return "Error: PropertyID is required."

        try:
            fields = [
                'Property ID', 'Type', 'Status', 'Street / Unit Number',
                'Location', 'Building/Subdivision', 'Owner', 'Price',
                'Lot Area', 'Floor Area', 'Bedrooms', 'Bathrooms',
                'Furnishing', 'Parking', 'Listing Title', 'Keyword',
                'Listing Description', 'Folder Path'
            ]

            print(f"Attempting to access table ID '{AirtableDataHelper.TABLE_ID}' with view '{AirtableDataHelper.VIEW_TABLE}'...")
            table = AirtableDataHelper.get_table()
            
            # Fetch the record with the matching Property ID from the specified view
            records = table.all(view=AirtableDataHelper.VIEW_TABLE, fields=fields, formula=f"{{Property ID}} = '{propertyID}'")

            if not records:
                print(f"Error: Property ID {propertyID} not found")
                return False

            record = records[0]['fields']

            listing_description = record.get('Listing Description', '')
            extracted_property_id = AirtableDataHelper.extract_property_id(listing_description)
            stored_property_id = record.get('Property ID')

            if extracted_property_id and stored_property_id:
                if extracted_property_id != stored_property_id:
                    print(f"Warning: Extracted Property ID ({extracted_property_id}) does not match stored Property ID ({stored_property_id})")
            elif extracted_property_id:
                record['Property ID'] = extracted_property_id
            elif not stored_property_id:
                print(f"Warning: No Property ID found for record: {record.get('Listing Title', 'Unknown Title')}")
            
            all_data = {
                "property_id": record.get('Property ID', ''),
                "folder_path": record.get('Folder Path', ''),
                "type": record.get('Type', ''),
                "status": record.get('Status', ''),
                "street_unit_no": record.get('Street / Unit Number', ''),
                "location": record.get('Location', ''),
                "building_subdivision": record.get('Building/Subdivision', ''),
                "owner": record.get('Owner', ''), 
                "price": record.get('Price', ''),
                "lot_area": record.get('Lot Area', ''),
                "floor_area": record.get('Floor Area', ''),
                "bedrooms": record.get('Bedrooms', ''),
                "bathrooms": record.get('Bathrooms', ''),
                "furnishing": record.get('Furnishing', ''),
                "parking": record.get('Parking', ''),
                "listing_title": record.get('Listing Title', ''),
                "keyword": record.get('Keyword', ''),
                "listing_description": record.get('Listing Description', '')
            }

            return all_data

        except Exception as e:
            return f"Error fetching data from Airtable API: {str(e)}"