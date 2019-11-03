rm -r dist/ build/
pyinstaller soundboard.spec
staticx dist/soundboard dist/soundboard.static
