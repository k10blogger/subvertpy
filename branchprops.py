# Copyright (C) 2006-2007 Jelmer Vernooij <jelmer@samba.org>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""Branch property access and caching."""

from bzrlib.errors import NoSuchRevision
from bzrlib.trace import mutter

from svn.core import SubversionException, Pool
import svn.core


class PathPropertyProvider:
    def __init__(self, log):
        self.log = log

    def get_properties(self, path, revnum):
        """Obtain all the directory properties set on a path/revnum pair.

        :param path: Subversion path
        :param revnum: Subversion revision number
        :return: Dictionary with properties
        """
        assert isinstance(path, str)
        path = path.lstrip("/")

        try:
            (_, _, props) = self.log._get_transport().get_dir(path, 
                revnum)
        except SubversionException, (_, num):
            if num == svn.core.SVN_ERR_FS_NO_SUCH_REVISION:
                raise NoSuchRevision(self, revnum)
            raise

        return props

    def get_changed_properties(self, path, revnum):
        """Get the contents of a Subversion file property.

        Will use the cache.

        :param path: Subversion path.
        :param revnum: Subversion revision number.
        :return: Contents of property or default if property didn't exist.
        """
        assert isinstance(revnum, int)
        assert isinstance(path, str)
        if not self.log.touches_path(path, revnum):
            return {}
        current = self.get_properties(path, revnum)
        if current == {}:
            return {}
        (prev_path, prev_revnum) = self.log.get_previous(path, revnum)
        if prev_path is None and prev_revnum == -1:
            previous = {}
        else:
            previous = self.get_properties(prev_path.encode("utf-8"), 
                                           prev_revnum)
        ret = {}
        for key, val in current.items():
            if previous.get(key) != val:
                ret[key] = val
        return ret

    def get_property_diff(self, path, revnum, name):
        """Returns the new lines that were added to a particular property."""
        assert isinstance(path, str)
        # If the path this property is set on didn't change, then 
        # the property can't have changed.
        if not self.log.touches_path(path, revnum):
            return ""

        current = self.get_properties(path, revnum).get(name, "")
        (prev_path, prev_revnum) = self.log.get_previous(path, revnum)
        if prev_path is None and prev_revnum == -1:
            previous = ""
        else:
            previous = self.get_properties(prev_path.encode("utf-8"), prev_revnum).get(name, "")
        if len(previous) > len(current) or current[0:len(previous)] != previous:
            mutter('original part changed for %r between %s:%d -> %s:%d' % (name, prev_path, prev_revnum, path, revnum))
            return ""
        return current[len(previous):] 

