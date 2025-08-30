import argparse, bcrypt, getpass

def make_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--password", help="Plaintext password (optional, safer to enter interactively)")
    args = parser.parse_args()

    pw = args.password or getpass.getpass("Enter new admin password: ")
    print(make_hash(pw))
