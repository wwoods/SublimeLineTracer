
import re
import sublime
import sublime_plugin

"""This comment is for testing:

/tmp/blah.txt
Hey here's a file: /tmp/blah.txt
"/tmp/blah there.txt"
"/tmp/blah there.txt", line 12
/tmp/blah:12
"/tmp/blah there.txt":113

./blah.txt

In file /tmp/blah:
  12: Hey
  18: Yo there

"""

class LineTracerGotoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        target = self.view.settings().get('line_tracer_target')
        print(target)
        window = self.view.window()
        window.open_file(target, sublime.ENCODED_POSITION | sublime.TRANSIENT)

    def is_enabled(self):
        return self.view.settings().get('line_tracer_has_target', False)

    def is_visible(self):
        """This is never a menu command"""
        return False


class LineTracerWatcher(sublime_plugin.EventListener):
    def on_selection_modified(self, view):
        """See if we're on a line with a file / line that may be gone to.
        """
        target = None

        cursor = view.sel()[0]
        lineRegion = view.line(cursor)
        line = view.substr(lineRegion)

        view.erase_regions("line_tracer")
        foundRegions = []

        # Does our line have a filename?
        f = self._matchFile(line)
        if f is not None:
            foundRegions.append(sublime.Region(lineRegion.a + f.start(),
                    lineRegion.a + f.end()))
            target = f.group(0).replace('"', '')
            lineno = re.search(r"""(^:\d+|line \d+)""", line[f.end():], re.I)
            if lineno is not None:
                lpos = lineRegion.a + f.end()
                foundRegions.append(sublime.Region(lpos + lineno.start(),
                        lpos + lineno.end()))
                lineno = re.search("\d+", lineno.group(0))
                target += ':' + lineno.group(0)
        else:
            # Maybe we have a line number...
            l = re.search("[ \t]*(\d+):", line)
            if l is not None:
                foundRegions.append(sublime.Region(lineRegion.a + l.start(1),
                        lineRegion.a + l.end(1)))
                # Look backwards for a file
                lline = lineRegion
                while lline.a > 0:
                    lline = view.line(lline.a - 1)
                    f = self._matchFile(view.substr(lline))
                    if f is not None:
                        foundRegions.append(sublime.Region(lline.a + f.start(),
                                lline.a + f.end()))
                        target = f.group(0).replace('"', '') + ':' + l.group(1)
                        break

        if target and foundRegions:
            view.add_regions("line_tracer", foundRegions, "comment",
                    "", sublime.DRAW_EMPTY | sublime.HIDE_ON_MINIMAP)

        view.settings().set('line_tracer_target', target)
        view.settings().set('line_tracer_has_target', target is not None)


    def _matchFile(self, line):
        """Returns a regex match for the filename in the given line.
        """
        return re.search(r"""("(\.\./|\./|/)[^"]+"|(\.\./|\./|/)[^ \t\n:]+)""",
                line)
