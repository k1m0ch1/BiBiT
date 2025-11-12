"""
Test script for Klik Indomaret API
Tests the API endpoints before implementing in production
"""

import requests
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class KlikIndomaretAPITest:
    """Test class for Klik Indomaret API"""

    BASE_URL = "https://ap-mc.klikindomaret.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://www.klikindomaret.com/',
            'Origin': 'https://www.klikindomaret.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Priority': 'u=1, i',
        })

        self.default_params = {
            'storeCode': 'TJKT',
            'latitude': '-6.1763897',
            'longitude': '106.82667',
            'mode': 'DELIVERY',
            'districtId': '141100100'
        }

    def test_category_api(self):
        """Test 1: Category API endpoint"""
        print("\n" + "="*60)
        print("TEST 1: Category API Endpoint")
        print("="*60)

        url = f"{self.BASE_URL}/assets-klikidmgroceries/api/get/catalog-xpress/api/webapp/category/meta"

        try:
            response = self.session.get(url, params=self.default_params, timeout=10)
            response.raise_for_status()

            data = response.json()
            categories = data.get('data', [])

            print(f"[OK] Status Code: {response.status_code}")
            print(f"[OK] Total Categories: {len(categories)}")
            print(f"\nFirst 3 categories:")
            for i, cat in enumerate(categories[:3]):
                print(f"  {i+1}. {cat.get('label', 'Unknown')} (ID: {cat.get('id')})")

            return True, categories

        except Exception as e:
            print(f"[FAIL] Error: {str(e)}")
            return False, []

    def test_product_api(self, category_id=None):
        """Test 2: Product API endpoint"""
        print("\n" + "="*60)
        print("TEST 2: Product Search API Endpoint")
        print("="*60)

        url = f"{self.BASE_URL}/assets-klikidmcore/api/get/catalog-xpress/api/webapp/search/result"

        params = {
            **self.default_params,
            'page': 0,
            'size': 10,
            'categories': category_id or ''
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            products = data.get('data', [])
            total_elements = data.get('totalElements', 0)
            total_pages = data.get('totalPages', 0)

            print(f"[OK] Status Code: {response.status_code}")
            print(f"[OK] Total Products: {total_elements}")
            print(f"[OK] Total Pages: {total_pages}")
            print(f"[OK] Products in this page: {len(products)}")

            if products:
                print(f"\nFirst product sample:")
                product = products[0]
                print(f"  ID: {product.get('id')}")
                print(f"  Name: {product.get('name')}")
                print(f"  SKU: {product.get('sku', 'N/A')}")

                prices = product.get('prices', [])
                if prices:
                    price_info = prices[0]
                    print(f"  Price: Rp {price_info.get('price', 0):,}")
                    if price_info.get('originalPrice', 0) > price_info.get('price', 0):
                        print(f"  Original Price: Rp {price_info.get('originalPrice', 0):,}")
                        print(f"  Discount: {price_info.get('discount', 'N/A')}")

            return True, data

        except Exception as e:
            print(f"[FAIL] Error: {str(e)}")
            return False, {}

    def test_pagination(self):
        """Test 3: Pagination"""
        print("\n" + "="*60)
        print("TEST 3: Pagination")
        print("="*60)

        url = f"{self.BASE_URL}/assets-klikidmcore/api/get/catalog-xpress/api/webapp/search/result"

        try:
            # Test page 0
            params = {**self.default_params, 'page': 0, 'size': 5, 'categories': ''}
            response1 = self.session.get(url, params=params, timeout=10)
            response1.raise_for_status()
            data1 = response1.json()

            # Test page 1
            params['page'] = 1
            response2 = self.session.get(url, params=params, timeout=10)
            response2.raise_for_status()
            data2 = response2.json()

            products1 = data1.get('data', [])
            products2 = data2.get('data', [])

            print(f"[OK] Page 0 products: {len(products1)}")
            print(f"[OK] Page 1 products: {len(products2)}")

            # Check if products are different
            if products1 and products2:
                id1 = products1[0].get('id')
                id2 = products2[0].get('id')
                if id1 != id2:
                    print(f"[OK] Pagination working (different products per page)")
                    return True
                else:
                    print(f"[WARN] Pagination might not be working (same products)")
                    return False

            return True

        except Exception as e:
            print(f"[FAIL] Error: {str(e)}")
            return False

    def test_category_filter(self, category_id):
        """Test 4: Category filtering"""
        print("\n" + "="*60)
        print(f"TEST 4: Category Filter (ID: {category_id})")
        print("="*60)

        url = f"{self.BASE_URL}/assets-klikidmcore/api/get/catalog-xpress/api/webapp/search/result"

        params = {
            **self.default_params,
            'page': 0,
            'size': 5,
            'categories': category_id
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            products = data.get('data', [])
            total = data.get('totalElements', 0)

            print(f"[OK] Status Code: {response.status_code}")
            print(f"[OK] Products in category: {total}")
            print(f"[OK] Sample products: {len(products)}")

            return True

        except Exception as e:
            print(f"[FAIL] Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("KLIK INDOMARET API TESTING")
        print("="*60)

        results = {}

        # Test 1: Categories
        success, categories = self.test_category_api()
        results['categories'] = success

        # Test 2: Products (all categories)
        success, data = self.test_product_api()
        results['products'] = success

        # Test 3: Pagination
        success = self.test_pagination()
        results['pagination'] = success

        # Test 4: Category filter (if we have categories)
        if categories:
            first_category_id = categories[0].get('id')
            success = self.test_category_filter(first_category_id)
            results['category_filter'] = success

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        all_passed = all(results.values())

        for test_name, passed in results.items():
            status = "[PASS]" if passed else "[FAIL]"
            print(f"{status}: {test_name}")

        print("\n" + "="*60)
        if all_passed:
            print("[SUCCESS] ALL TESTS PASSED - API is ready to use!")
        else:
            print("[ERROR] SOME TESTS FAILED - Review errors above")
        print("="*60)

        return all_passed


if __name__ == "__main__":
    tester = KlikIndomaretAPITest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
