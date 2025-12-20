import hashlib
import sys

def generate_hash(password):
    """Generates SHA256 hash for the given password."""
    return hashlib.sha256(password.encode()).hexdigest()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pwd = sys.argv[1]
    else:
        pwd = input("Enter new password to hash: ")
        
    print(f"\nPassword: {pwd}")
    print(f"SHA256 Hash: {generate_hash(pwd)}")
    print("\nCopy this hash and replace MASTER_HASH in dashboard/app.py")
