# delete_incidents.py
import requests
from app.config import SNOW_INSTANCE, SNOW_USERNAME, SNOW_PASSWORD

def delete_recent_incidents(count=54):
    """
    Delete the most recent incidents from ServiceNow
    """
    BASE_URL = f"https://{SNOW_INSTANCE}.service-now.com/api/now/table/incident"
    
    print(f"Connecting to ServiceNow instance: {SNOW_INSTANCE}")
    
    try:
        # First, get the most recent incidents
        print(f"Fetching last {count} incidents...")
        
        response = requests.get(
            BASE_URL,
            auth=(SNOW_USERNAME, SNOW_PASSWORD),
            headers={"Content-Type": "application/json"},
            params={
                "sysparm_query": "ORDERBYDESCsys_created_on",  # Get newest first
                "sysparm_limit": count,
                "sysparm_fields": "sys_id,number,short_description,sys_created_on"
            }
        )
        
        response.raise_for_status()
        incidents = response.json().get("result", [])
        
        if not incidents:
            print("No incidents found!")
            return
        
        print(f"Found {len(incidents)} incidents. Starting deletion...")
        print("-" * 80)
        
        deleted_count = 0
        failed_count = 0
        
        for incident in incidents:
            incident_number = incident.get("number", "Unknown")
            short_desc = incident.get("short_description", "")[:50]
            sys_id = incident.get("sys_id")
            
            print(f"Deleting INC {incident_number}: {short_desc}...")
            
            try:
                # Delete the incident
                delete_response = requests.delete(
                    f"{BASE_URL}/{sys_id}",
                    auth=(SNOW_USERNAME, SNOW_PASSWORD),
                    headers={"Content-Type": "application/json"}
                )
                
                if delete_response.status_code in [200, 204]:
                    print(f"  ✅ Deleted INC {incident_number}")
                    deleted_count += 1
                else:
                    print(f"  ❌ Failed to delete INC {incident_number}: Status {delete_response.status_code}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"  ❌ Error deleting INC {incident_number}: {e}")
                failed_count += 1
        
        print("-" * 80)
        print(f"Deletion complete!")
        print(f"✅ Successfully deleted: {deleted_count} incidents")
        print(f"❌ Failed to delete: {failed_count} incidents")
        
        # Also delete from tickets collection if it exists
        # delete_from_tickets_collection(incidents)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to ServiceNow: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def delete_from_tickets_collection(incidents):
    """
    Delete corresponding records from MongoDB tickets collection
    """
    try:
        from app.db import tickets_col
        
        deleted_in_db = 0
        for incident in incidents:
            ticket_number = incident.get("number")
            if ticket_number:
                result = tickets_col.delete_many({
                    "ticket_number": ticket_number
                })
                deleted_in_db += result.deleted_count
        
        print(f"🗑️  Removed {deleted_in_db} records from tickets collection")
        
    except Exception as e:
        print(f"Note: Could not delete from tickets collection: {e}")

def delete_specific_incidents(incident_numbers):
    """
    Delete specific incidents by their numbers
    """
    BASE_URL = f"https://{SNOW_INSTANCE}.service-now.com/api/now/table/incident"
    
    print(f"Deleting specific incidents: {incident_numbers}")
    
    deleted_count = 0
    failed_count = 0
    
    for inc_number in incident_numbers:
        try:
            # First find the incident by number
            response = requests.get(
                BASE_URL,
                auth=(SNOW_USERNAME, SNOW_PASSWORD),
                params={"sysparm_query": f"number={inc_number}"}
            )
            
            response.raise_for_status()
            incidents = response.json().get("result", [])
            
            if incidents:
                sys_id = incidents[0].get("sys_id")
                
                # Delete the incident
                delete_response = requests.delete(
                    f"{BASE_URL}/{sys_id}",
                    auth=(SNOW_USERNAME, SNOW_PASSWORD)
                )
                
                if delete_response.status_code in [200, 204]:
                    print(f"✅ Deleted {inc_number}")
                    deleted_count += 1
                else:
                    print(f"❌ Failed to delete {inc_number}")
                    failed_count += 1
            else:
                print(f"⚠️  Incident {inc_number} not found")
                failed_count += 1
                
        except Exception as e:
            print(f"❌ Error deleting {inc_number}: {e}")
            failed_count += 1
    
    print(f"\nDeleted: {deleted_count}, Failed: {failed_count}")

def show_recent_incidents(limit=60):
    """
    Show recent incidents without deleting them
    """
    BASE_URL = f"https://{SNOW_INSTANCE}.service-now.com/api/now/table/incident"
    
    try:
        response = requests.get(
            BASE_URL,
            auth=(SNOW_USERNAME, SNOW_PASSWORD),
            params={
                "sysparm_query": "ORDERBYDESCsys_created_on",
                "sysparm_limit": limit,
                "sysparm_fields": "number,short_description,category,sys_created_on,state"
            }
        )
        
        response.raise_for_status()
        incidents = response.json().get("result", [])
        
        print(f"\n{'='*80}")
        print(f"LAST {len(incidents)} INCIDENTS")
        print(f"{'='*80}")
        
        for i, incident in enumerate(incidents, 1):
            number = incident.get("number", "Unknown")
            desc = incident.get("short_description", "")[:60]
            category = incident.get("category", "")
            created = incident.get("sys_created_on", "")[:10]
            state = incident.get("state", "")
            
            print(f"{i:3}. {number:12} | {desc:60} | {category:15} | {created} | {state}")
        
        print(f"{'='*80}")
        print(f"Total incidents shown: {len(incidents)}")
        
        return incidents
        
    except Exception as e:
        print(f"Error fetching incidents: {e}")
        return []

def delete_incidents_by_creation_date(days_ago=1):
    """
    Delete incidents created within the last X days
    """
    BASE_URL = f"https://{SNOW_INSTANCE}.service-now.com/api/now/table/incident"
    
    # Calculate date (ServiceNow uses sys_created_on)
    import datetime
    cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    query = f"sys_created_on>={cutoff_date}"
    
    print(f"Deleting incidents created since {cutoff_date}")
    
    try:
        # First get all incidents after cutoff date
        response = requests.get(
            BASE_URL,
            auth=(SNOW_USERNAME, SNOW_PASSWORD),
            params={
                "sysparm_query": query,
                "sysparm_limit": 1000
            }
        )
        
        response.raise_for_status()
        incidents = response.json().get("result", [])
        
        print(f"Found {len(incidents)} incidents created since {cutoff_date}")
        
        if input(f"Delete all {len(incidents)} incidents? (yes/no): ").lower() != "yes":
            print("Cancelled")
            return
        
        deleted_count = 0
        for incident in incidents:
            sys_id = incident.get("sys_id")
            number = incident.get("number", "Unknown")
            
            try:
                delete_response = requests.delete(
                    f"{BASE_URL}/{sys_id}",
                    auth=(SNOW_USERNAME, SNOW_PASSWORD)
                )
                
                if delete_response.status_code in [200, 204]:
                    print(f"✅ Deleted {number}")
                    deleted_count += 1
                else:
                    print(f"❌ Failed to delete {number}")
                    
            except Exception as e:
                print(f"❌ Error deleting {number}: {e}")
        
        print(f"\nDeleted {deleted_count} incidents created since {cutoff_date}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    
    print("=" * 80)
    print("SERVICENOW INCIDENT CLEANUP TOOL")
    print("=" * 80)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "show":
            show_recent_incidents(60)
        elif sys.argv[1] == "date":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            delete_incidents_by_creation_date(days)
        elif sys.argv[1] == "specific":
            incidents = sys.argv[2:]
            delete_specific_incidents(incidents)
        else:
            count = int(sys.argv[1])
            delete_recent_incidents(count)
    else:
        # Show menu
        print("\nOptions:")
        print("1. Delete last N incidents (default: 54)")
        print("2. Show recent incidents without deleting")
        print("3. Delete incidents by creation date")
        print("4. Delete specific incidents by number")
        
        choice = input("\nChoose option (1-4): ").strip()
        
        if choice == "1":
            count = input("How many incidents to delete? (default 54): ").strip()
            count = int(count) if count else 54
            delete_recent_incidents(count)
        elif choice == "2":
            limit = input("How many to show? (default 60): ").strip()
            limit = int(limit) if limit else 60
            show_recent_incidents(limit)
        elif choice == "3":
            days = input("Delete incidents created in last how many days? (default 1): ").strip()
            days = int(days) if days else 1
            delete_incidents_by_creation_date(days)
        elif choice == "4":
            numbers = input("Enter incident numbers separated by spaces (e.g., INC0010117 INC0010118): ").strip().split()
            delete_specific_incidents(numbers)
        else:
            # Default: delete last 54 incidents
            print("\nDeleting last 54 incidents...")
            delete_recent_incidents(54)