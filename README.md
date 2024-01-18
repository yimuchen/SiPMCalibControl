# SiPM Calibration control software

Software used for the data collection of the SiPM calibration gantry system
developed by UMD. Documentations found in the repository files will mainly
be used to describe coding and programming technical details regarding the
control software. See the following links for other documentations related to
the SiPM calibration project.

Notice that this package will not contain the analysis code required for
detailed results analysis. That is hosted on a separate repository
[here][sipmanalyze].

## Quickly overview of documentation

- [Operation manual][manual]: Primary manual that should be used by the
  operators. Require minimum knowledge of the package in general.
- [Development instructions][dev_manual]: General information about how to
  navigate the various source code directories, as well as links to resources
  on learning the technologies in this package.
  - [Deployment instructions][deploy]: Quick instructions for setting up the
    environment for local testing and development.

## Quick overview of code-base navigation

- [`bin`](bin): User-level executable, see the official [manual][manual] for
  more detailed instructions.
- [`scripts`](scripts): Assistance scripts for settings up secondary
  dependencies. The usage of these scripts should only be explicitly performed
  by the developers or administrators. For more details, see [development
  instructions][dev_manual].
- [`docs`](docs): Lists of structured manual. Notice that details of the
  individual technologies used for the code based will be hosted in their
  source code directories. Developer documentation here is mainly concerned
  with the designed decisions and interaction with various technologies.
- [`src`](src): Source code directory. Documentation of individual technologies
  should mainly be kept inline with the code where ever it makes sense.

[manual]: docs/manual
[dev_manual]: docs/dev/
[deploy]: docs/dev/deploy.md
[sipmanalyze]: https://github.com/UMDCMS/sipmanalyze
