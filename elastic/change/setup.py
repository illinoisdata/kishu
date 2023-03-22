from distutils.core import setup, Extension

def main():
    setup(name="idgraph",
          version="1.0.0",
          description="Python interface for the idgraph C library function",
          author="Pranav",
          author_email="gor2@illinois.edu",
          ext_modules=[Extension("idgraph", ["idgraphmodule.c"])])

if __name__ == "__main__":
    main()