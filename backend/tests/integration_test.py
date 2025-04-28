import requests
import time


def wait_for_backend(url, timeout=30):
    for _ in range(timeout):
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def test_backend_root():
    assert wait_for_backend("http://localhost:8000/")
    r = requests.get("http://localhost:8000/")
    assert r.status_code == 200
    assert "message" in r.json()


def test_list_microservices():
    r = requests.get("http://localhost:8000/list-microservices")
    assert r.status_code == 200
    assert "microservices" in r.json()


if __name__ == "__main__":
    test_backend_root()
    test_list_microservices()
    print("Integration tests passed!")
