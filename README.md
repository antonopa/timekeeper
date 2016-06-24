# timekeeper
Python package to keep track of working hours. This was written only with python3 in
mind and it's not expected/guaranteed to work with any older versions.

## Structure
This consists of a main package under `timekeeper` which includes the DB wrapper
class which handles all operations towards `SQLite`.
Under `timekeeper` there is also a `tools` subpackage including all the command line
tools to be able to handle the DB class.

* `tools.lockwatcher`: This connects to D-Bus signals listening on gnome-screensaver
  lock and unlock commands.
  - When the screen is locked it updates the end time of the current day. This assumes
  that the last screen lock is also the time when the user leaves the office.
  - When the screen is unlocked it tries to insert a new working day in the DB. If the
  day isn't there it is inserted, if it exists then the WorkTimeDB insert_day method
  handles the raised exception and prints out a message (safe to be ignored). If the
  insertion was successful this means that also the start time for the day was implicitly
  created thus marking the start of a working day.

* `tools.worktime`: `worktime` can be used to print reports out of the DB and provides
  some basic functions to add new days, update the lunch duration, etc. An extensive list
  of all options can be easily retrieves by calling it without arguments or with -h or
  --help.

## Creating a package
`tox` is your friend. Run `tox` in the repository root directory. The resulting package
can be installed with pip.

## Usage
The package creates three command line tools: `lockwatcher, worktime` and `wt`. The first is
a wrapper for the `tools.lockwatcher` and the other two call `tool.worktime`

* `lockwatcher` doesn't take any arguments and can be added in .xinitrc to monitor lock and
  unlock events
* `worktime` has a plethora of options which are documented in the script and can be seen by
  calling it without arguments or with {-h,--help}.
