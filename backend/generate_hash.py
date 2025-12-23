import argparse
import bcrypt
import getpass

def make_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")

def prompt_password() -> str:
    while True:
        pw1 = getpass.getpass("Enter new admin password: ")
        pw2 = getpass.getpass("Confirm password: ")
        if not pw1:
            print("❌ Password cannot be empty. Try again.\n")
            continue
        if pw1 != pw2:
            print("❌ Passwords do not match. Try again.\n")
            continue
        return pw1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--password", help="Plaintext password (optional)")
    args = parser.parse_args()

    pw = args.password if (args.password and args.password.strip()) else prompt_password()
    print(make_hash(pw))
