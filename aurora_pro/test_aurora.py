"""
Simple test script for Aurora Pro.
"""
import asyncio
import httpx


async def test_aurora():
    """Test Aurora API endpoints."""
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Testing Aurora Pro API...\n")

        # Test root endpoint
        print("1. Testing root endpoint...")
        response = await client.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")

        # Test health endpoint
        print("2. Testing health endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")

        # Test analyze endpoint with a valid URL
        print("3. Testing analyze endpoint with GitHub URL...")
        test_url = "https://github.com/pytorch/pytorch"
        response = await client.post(
            f"{base_url}/analyze",
            json={"url": test_url}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"   Evidence ID: {data['id']}")
            print(f"   Title: {data['title']}")
            print(f"   Score: {data['score']}")
            print(f"   Signals: {data['facets'].get('signals', [])}\n")

            # Test get evidence endpoint
            print("4. Testing get evidence endpoint...")
            evidence_id = data['id']
            response = await client.get(f"{base_url}/evidence/{evidence_id}")
            print(f"   Status: {response.status_code}")
            print(f"   Retrieved score: {response.json()['score']}\n")
        else:
            print(f"   Error: {response.text}\n")

        # Test list evidence endpoint
        print("5. Testing list evidence endpoint...")
        response = await client.get(f"{base_url}/evidence?limit=10")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Total: {data['total']}")
        print(f"   Results: {len(data['results'])}\n")

        # Test metrics endpoint
        print("6. Testing metrics endpoint...")
        response = await client.get(f"{base_url}/metrics")
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type')}")
        lines = response.text.split('\n')[:5]
        print(f"   First 5 lines of metrics:")
        for line in lines:
            if line:
                print(f"      {line}")

        print("\n✓ All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_aurora())