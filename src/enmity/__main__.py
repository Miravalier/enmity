from argparse import ArgumentParser

from .bot import Bot


def main():
    parser = ArgumentParser()
    parser.add_argument("token", help="Discord bot auth token")
    args = parser.parse_args()

    bot = Bot()
    bot.run(args.token)


if __name__ == "__main__":
    main()
