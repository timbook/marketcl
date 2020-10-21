from distutils.core import setup

def main():
    setup(
        name="marketcl",
        version="0.1",
        description="A fantasy stock trading app for the command line",
        author="Timothy Book",
        author_email="TimothyKBook@gmail.com",
        url="www.github.com/timbook/marketcl",
        license="GPL",
        install_requires=[
            "pandas",
            "numpy",
            "matplotlib",
            "yfinance"
        ],
        packages=(
            "marketcl",
            "marketcl.items",
            "marketcl.dialogues"
        ),
        scripts=["marketcl/marketcl"]
    )

if __name__ == "__main__":
    main()
