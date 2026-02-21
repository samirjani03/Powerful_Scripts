import requests
import webbrowser
import socket
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

class UltimateIPTracker:
    """
    COMPLETE UNLIMITED IP TRACKER - FIXED VERSION
    Handles both PUBLIC and PRIVATE IP addresses
    """
    
    def __init__(self):
        # List of free APIs with NO rate limits
        self.free_apis = [
            "http://ip-api.com/json/{ip}",
            "https://freeipapi.com/api/json/{ip}",
            "https://ipwho.is/{ip}",
            "https://api.ip.sb/geoip/{ip}",
            "https://ipapi.co/{ip}/json/",
            "https://api.db-ip.com/v2/free/{ip}"
        ]
        
        # Private IP ranges (for educational display)
        self.private_ranges = [
            ("10.0.0.0", "10.255.255.255"),
            ("172.16.0.0", "172.31.255.255"),
            ("192.168.0.0", "192.168.255.255")
        ]
    
    def is_private_ip(self, ip):
        """Check if IP is in private range"""
        try:
            ip_parts = list(map(int, ip.split('.')))
            
            # Check 10.0.0.0/8
            if ip_parts[0] == 10:
                return True
            
            # Check 172.16.0.0/12
            if ip_parts[0] == 172 and 16 <= ip_parts[1] <= 31:
                return True
            
            # Check 192.168.0.0/16
            if ip_parts[0] == 192 and ip_parts[1] == 168:
                return True
            
            return False
        except:
            return False
    
    def get_local_info(self, ip):
        """Get information for local/private IPs"""
        try:
            # Try to get hostname
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except:
                hostname = "Unknown"
            
            # Get network interface info
            import platform
            system = platform.system()
            
            if system == "Windows":
                # Windows command to get network info
                cmd = f"ipconfig | findstr /i {ip}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                interface_info = result.stdout[:200] if result.stdout else "Local Network"
            else:
                # Linux/Mac command
                cmd = f"ifconfig | grep -B2 {ip}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                interface_info = result.stdout[:200] if result.stdout else "Local Network"
            
            return {
                'ip': ip,
                'type': 'PRIVATE',
                'hostname': hostname,
                'network': 'Local Area Network (LAN)',
                'location': 'Cannot be geolocated (private IP)',
                'latitude': None,
                'longitude': None,
                'interface_info': interface_info,
                'educational_note': 'Private IPs are used within local networks and cannot be tracked externally.'
            }
        except Exception as e:
            return {
                'ip': ip,
                'type': 'PRIVATE',
                'error': str(e),
                'educational_note': 'This is a private IP address used within local networks.'
            }
    
    def query_single_api(self, api_url, ip):
        """Query a single API endpoint"""
        try:
            url = api_url.format(ip=ip)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Educational-IPTracker/1.0)',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return self.parse_api_response(data)
        
        except Exception as e:
            # Silently fail and try next API
            return None
        
        return None
    
    def parse_api_response(self, data):
        """Parse different API response formats"""
        # Try different key patterns from various APIs
        patterns = [
            ('lat', 'lon'),  # ip-api.com
            ('latitude', 'longitude'),  # freeipapi.com
            ('Latitude', 'Longitude'),  # Some APIs
            ('lat', 'lng'),  # ipwho.is
            ('location.lat', 'location.lng')  # Some have nested
        ]
        
        for lat_key, lon_key in patterns:
            # Handle nested keys
            if '.' in lat_key:
                keys = lat_key.split('.')
                lat = data
                for key in keys:
                    lat = lat.get(key, {})
            else:
                lat = data.get(lat_key)
            
            if '.' in lon_key:
                keys = lon_key.split('.')
                lon = data
                for key in keys:
                    lon = lon.get(key, {})
            else:
                lon = data.get(lon_key)
            
            if lat and lon:
                return {
                    'ip': data.get('query') or data.get('ip') or 'Unknown',
                    'city': data.get('city') or data.get('cityName') or 'Unknown',
                    'region': data.get('region') or data.get('regionName') or data.get('state') or 'Unknown',
                    'country': data.get('country') or data.get('countryName') or data.get('country_name') or 'Unknown',
                    'latitude': float(lat),
                    'longitude': float(lon),
                    'isp': data.get('isp') or data.get('org') or data.get('asn') or 'Unknown',
                    'timezone': data.get('timezone') or 'Unknown',
                    'zip': data.get('zip') or data.get('postal') or data.get('postalCode') or 'Unknown'
                }
        
        return None
    
    def get_public_ip_location(self, ip):
        """Get location for public IP using multiple APIs"""
        results = []
        
        # Try up to 3 APIs in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_api = {
                executor.submit(self.query_single_api, api, ip): api 
                for api in self.free_apis[:3]  # Try first 3 APIs
            }
            
            for future in as_completed(future_to_api):
                result = future.result()
                if result:
                    results.append(result)
        
        # Return the first successful result
        if results:
            # Find the result with most complete data
            best_result = max(results, key=lambda x: len([v for v in x.values() if v]))
            return best_result
        
        return None
    
    def get_location(self, ip_address):
        """Main method to get location for any IP"""
        print(f"\n🔍 Analyzing IP: {ip_address}")
        
        # Validate IP format
        if not self.is_valid_ip(ip_address):
            return {
                'error': f"'{ip_address}' is not a valid IP address format",
                'format': 'Expected format: xxx.xxx.xxx.xxx (0-255 for each octet)'
            }
        
        # Check if it's a private IP
        if self.is_private_ip(ip_address):
            print("⚠️  This is a PRIVATE IP address (LAN/Router)")
            return self.get_local_info(ip_address)
        
        # It's a public IP, try to geolocate
        print("🌍 This is a PUBLIC IP address, attempting geolocation...")
        result = self.get_public_ip_location(ip_address)
        
        if result:
            result['type'] = 'PUBLIC'
            return result
        else:
            return {
                'ip': ip_address,
                'type': 'PUBLIC',
                'error': 'Could not retrieve location information',
                'possible_reasons': [
                    'IP address may not exist',
                    'All geolocation APIs are temporarily unavailable',
                    'IP may be from a mobile network or VPN',
                    'Rate limits may have been exceeded (wait a minute)'
                ]
            }
    
    def is_valid_ip(self, ip):
        """Validate IP address format"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        for part in parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            except ValueError:
                return False
        
        return True
    
    def display_results(self, data):
        """Display results in a user-friendly format"""
        print("\n" + "="*60)
        print("📍 IP LOCATION TRACKER - EDUCATIONAL PURPOSES")
        print("="*60)
        
        if 'error' in data:
            print(f"\n❌ Error: {data['error']}")
            if 'format' in data:
                print(f"📝 {data['format']}")
            if 'possible_reasons' in data:
                print("\n📋 Possible reasons:")
                for reason in data['possible_reasons']:
                    print(f"   • {reason}")
            return False
        
        print(f"\n📡 IP Address: {data.get('ip', 'Unknown')}")
        print(f"🔒 Type: {data.get('type', 'Unknown')}")
        
        if data.get('type') == 'PRIVATE':
            print(f"🏠 Hostname: {data.get('hostname', 'Unknown')}")
            print(f"🌐 Network: {data.get('network', 'Unknown')}")
            print(f"📍 {data.get('location', '')}")
            print(f"\n📚 {data.get('educational_note', '')}")
            
            if 'interface_info' in data and data['interface_info']:
                print(f"\n🔧 Interface Info:")
                print(data['interface_info'][:200] + "...")
        
        else:  # PUBLIC IP
            print(f"🏙️  City: {data.get('city', 'Unknown')}")
            print(f"📍 Region/State: {data.get('region', 'Unknown')}")
            print(f"🌎 Country: {data.get('country', 'Unknown')}")
            print(f"📮 ZIP/Postal Code: {data.get('zip', 'Unknown')}")
            print(f"🕐 Timezone: {data.get('timezone', 'Unknown')}")
            print(f"📡 ISP/Organization: {data.get('isp', 'Unknown')}")
            
            lat = data.get('latitude')
            lon = data.get('longitude')
            if lat and lon:
                print(f"🎯 Coordinates: {lat}, {lon}")
                
                # Show accuracy estimate
                if data.get('type') == 'PUBLIC':
                    print(f"📊 Estimated Accuracy: City-level (~1-10 km radius)")
                    print(f"💡 Note: IP geolocation is approximate, not exact GPS")
        
        print("\n" + "="*60)
        return True
    
    def open_google_maps(self, latitude, longitude, zoom=15):
        """Open Google Maps with the location"""
        if latitude and longitude:
            # Google Maps URL with precise coordinates
            maps_url = f"https://www.google.com/maps/@{latitude},{longitude},{zoom}z"
            
            print(f"\n🌍 Opening Google Maps...")
            print(f"📌 Direct link: {maps_url}")
            
            # Open in default browser
            webbrowser.open(maps_url)
            
            # Also show alternative mapping services
            print(f"\n🔗 Alternative maps:")
            print(f"   • OpenStreetMap: https://www.openstreetmap.org/#map=15/{latitude}/{longitude}")
            print(f"   • Bing Maps: https://www.bing.com/maps?cp={latitude}~{longitude}&lvl=15")
            
            return maps_url
        
        print("❌ Cannot open maps: No coordinates available")
        return None
    
    def save_results(self, data, filename=None):
        """Save results to a file"""
        if filename is None:
            filename = f"ip_tracker_{data.get('ip', 'unknown')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("IP LOCATION TRACKER RESULTS\n")
                f.write(f"Generated: {self.get_current_time()}\n")
                f.write("="*60 + "\n\n")
                
                for key, value in data.items():
                    if value:  # Only write non-empty values
                        f.write(f"{key.upper():<20}: {value}\n")
                
                f.write("\n" + "="*60 + "\n")
                f.write("Note: For educational purposes only\n")
                f.write("Respect privacy and use responsibly\n")
            
            print(f"💾 Results saved to: {filename}")
            return True
        
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return False
    
    def get_current_time(self):
        """Get current date and time"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_own_public_ip(self):
        """Get user's own public IP address"""
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            return response.json()['ip']
        except:
            try:
                response = requests.get('https://ipinfo.io/ip', timeout=5)
                return response.text.strip()
            except:
                return None

# Main program
def main():
    print("🌐 ULTIMATE UNLIMITED IP TRACKER")
    print("="*60)
    print("Note: This tool is for EDUCATIONAL purposes only!")
    print("="*60)
    
    tracker = UltimateIPTracker()
    
    while True:
        print("\n" + "="*60)
        print("OPTIONS:")
        print("1. Track an IP address")
        print("2. Track my own public IP")
        print("3. Test with example IPs (8.8.8.8, 1.1.1.1)")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            ip_address = input("Enter IP address to track: ").strip()
            
            # Remove http/https if accidentally entered
            if ip_address.startswith(('http://', 'https://')):
                ip_address = ip_address.split('//')[1].split('/')[0]
            
            result = tracker.get_location(ip_address)
            
            if tracker.display_results(result):
                # Check if we have coordinates for maps
                if result.get('latitude') and result.get('longitude'):
                    open_map = input("\nOpen location in Google Maps? (y/n): ").lower()
                    if open_map == 'y':
                        tracker.open_google_maps(result['latitude'], result['longitude'])
                
                # Ask to save results
                save_results = input("\nSave results to file? (y/n): ").lower()
                if save_results == 'y':
                    tracker.save_results(result)
        
        elif choice == '2':
            print("\n🔍 Getting your public IP address...")
            own_ip = tracker.get_own_public_ip()
            
            if own_ip:
                print(f"📱 Your Public IP: {own_ip}")
                
                confirm = input(f"Track this IP? (y/n): ").lower()
                if confirm == 'y':
                    result = tracker.get_location(own_ip)
                    
                    if tracker.display_results(result):
                        if result.get('latitude') and result.get('longitude'):
                            open_map = input("\nOpen your location in Google Maps? (y/n): ").lower()
                            if open_map == 'y':
                                tracker.open_google_maps(result['latitude'], result['longitude'])
                        
                        save_results = input("\nSave results to file? (y/n): ").lower()
                        if save_results == 'y':
                            tracker.save_results(result)
            else:
                print("❌ Could not retrieve your public IP")
        
        elif choice == '3':
            print("\n📚 Example IP Addresses for Testing:")
            examples = [
                ("8.8.8.8", "Google DNS - Mountain View, California"),
                ("1.1.1.1", "Cloudflare DNS - Global"),
                ("208.67.222.222", "OpenDNS - Various locations"),
                ("139.130.4.5", "AARNet - Australia"),
                ("203.12.160.35", "Australia Network")
            ]
            
            for i, (ip, desc) in enumerate(examples, 1):
                print(f"{i}. {ip} - {desc}")
            
            example_choice = input("\nEnter example number (1-5) or IP: ").strip()
            
            if example_choice.isdigit() and 1 <= int(example_choice) <= 5:
                ip_address = examples[int(example_choice)-1][0]
            else:
                ip_address = example_choice
            
            result = tracker.get_location(ip_address)
            
            if tracker.display_results(result):
                if result.get('latitude') and result.get('longitude'):
                    open_map = input("\nOpen location in Google Maps? (y/n): ").lower()
                    if open_map == 'y':
                        tracker.open_google_maps(result['latitude'], result['longitude'])
        
        elif choice == '4':
            print("\n👋 Thank you for using the IP Tracker!")
            print("Remember: Use this tool responsibly for educational purposes only.")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")

# Check if required packages are installed
def check_dependencies():
    required = ['requests']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("❌ Missing required packages!")
        print("Please install them using:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

if __name__ == "__main__":
    if check_dependencies():
        try:
            main()
        except KeyboardInterrupt:
            print("\n\n⚠️  Program interrupted by user")
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please try again or report this issue.")
    else:
        input("\nPress Enter to exit...")
