# biobox-analytics
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "biobox_analytics"
version = "0.1.6"
description = "BioBox CLI for data manipulation in python"
readme = "README.md"
readme-content-type = "text/markdown"  # Specify content type for Markdown
license = { text = "MIT" }
authors = [
    {name = "Christopher Li", email = "chris@biobox.io"},
    {name = "Hamza Farooq", email = "hamza@biobox.io"},
    {name = "Julian Mazzitelli", email = "julian@biobox.io"}
]
requires-python = ">=3.10"
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent"
]
dependencies = [
  "scanpy",
  "gtfparse",
  "pandas"
]
urls = { "Homepage" = "https://github.com/biobox-analytics/biobox_analytics" }