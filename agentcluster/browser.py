import os;
import stat;
import logging

__all__ = ["Any", "AnyJsonDecoder", "Browser", "AgentBrowser"]
logger = logging.getLogger('agentcluster.browser')

class Browser:
    """
        General file browser from a given list of filesystem objects.
    """
    def __init__(self):
        # Conf files found after call to browse()
        self.foundFiles = [];

    def browse (self, fsElements):
        for fsElement in fsElements:
            fsElement = os.path.abspath(fsElement);
            self.startBrowsing(fsElement);
            topLen = len(fsElement.split(os.path.sep))
            self._browse(fsElement, topLen)

    def _browse (self, fsElement, topLen):

        if not os.path.exists(fsElement):
            return

        inode = os.lstat(fsElement)
        if stat.S_ISREG(inode.st_mode):
            # Notify of the found file
            self.foundFile(fsElement);
            return

        for dFile in os.listdir(fsElement):
            fullPath = fsElement + os.path.sep + dFile
            inode = os.lstat(fullPath)
            if stat.S_ISDIR(inode.st_mode):
                # Recurse into subdirs
                self._browse( fullPath, topLen)
                continue            
            if not stat.S_ISREG(inode.st_mode):
                continue

            # Notify of the found file
            fullPath = os.path.abspath(fullPath);
            self.foundFile(fullPath);

    def foundFile (self, filePath, topLen=None):
        """ Callback called by browse() each time a file is encountered """
        # Default implementation store the file without condition
        self.foundFiles.append(filePath);
        pass;

    def startBrowsing (self, filePath):
        """ Callback called by browse() just before a new input directory is scanned """
        # Default implementation do nothing
        pass;


class AgentBrowser(Browser):
    """ Search for agent configuration files """

    ext = 'agent';

    def startBrowsing (self, filePath):
        logger.debug ( 'Searching for agent specifications in %s', filePath );
        pass;

    def foundFile (self, filePath, topLen=None):
        dExt = os.path.splitext(filePath)[1][1:]
        if dExt in [self.ext]:
            self.foundFiles.append(filePath);
        pass;

