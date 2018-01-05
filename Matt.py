# Copyright (c) 2017 Paul Ellis

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import getopt
import sys
import os

# Either python doesn't provide an OS-agnostic return code abstraction
# or I can't find it
class OsReturn:
   ok = 0
   error = 1

class IoDesc(object):
   ok = 0
   fileError = 1
   noMoreFiles = 2

   useStd = False
   fileNames = []
   fileNameIndex = 0

   def __init__(self, fileNamesArg):
      if len(fileNamesArg) == 0 or fileNamesArg[0] == "":
         self.useStd = True
      else:
         self.fileNames = fileNamesArg

   def read(self):
      return ""

   def write(self, outString):
      return OsReturn.ok

class IDesc(IoDesc):

   def __init__(self, fileNamesArg=[]):
      IoDesc.__init__(self, fileNamesArg)

   def read(self):
      if self.useStd:
         print "stdin not supported for input yet"
         return self.fileError, "", ""

      if self.fileNameIndex == len(self.fileNames):
         return self.noMoreFiles, "", ""

      outStr = ""
      try:
         with open(self.fileNames[self.fileNameIndex], "r") as fd:
            outStr = fd.read()
      except IOError:
         print "Could not read file " + self.fileNames[self.fileNameIndex]
         return self.fileError, "", ""

      self.fileNameIndex += 1

      return self.ok, self.fileNames[self.fileNameIndex - 1], outStr

class ODesc(IoDesc):
   firstWriteDone = False

   def __init__(self, fileNamesArg=""):
      IoDesc.__init__(self, [fileNamesArg])

   def write(self, outString):
      if self.useStd:
         sys.stdout.write(outString)
         return self.ok

      if type(self.fileNames[0]) is list:
         return self.fileError

      try:
         if self.firstWriteDone:
            with open(self.fileNames[0], "a") as fd:
               fd.write(outString)
         else:
            with open(self.fileNames[0], "w") as fd:
               fd.write(outString)
               self.firstWriteDone = True
      except IOError:
         print "Could not read file " + self.fileNames[0]
         return self.fileError, "", ""

      return self.ok

class MetrologyReportToken(object):
   __columnOffset = 0
   __columnWidth = 0
   __rowOffset = 0
   columnOffset = 0
   columnWidth = 0
   rowOffset = 0
   name = ""

   def __init__(self, name = "", columnOffset = 0,
                columnWidth = 0, rowOffset = 0):
      self.name = name
      self.__columnOffset = columnOffset
      self.__columnWidth = columnWidth
      self.__rowOffset = rowOffset

   def find(self, fname, strLines):

      if (len(strLines) < self.__rowOffset):
         print("Error: Invalid token (" + self.name + ") " +
               "with row offset (" + str(self.__rowOffset) + ") " +
               "for file " + fname)
         return OsReturn.error

      if (len(strLines[self.__rowOffset]) <= 
              self.__columnOffset + self.__columnWidth):
         print("Error: Invalid token (" + self.name + ") " +
               "with column offset (" + str(self.__rowOffset) + ") " +
               "or column width (" + str(self.__columnWidth) + ") " +
               "for file " + fname)
         return OsReturn.error


      # how's this for "parsing?" XD
      self.columnOffset = self.__columnOffset
      self.columnWidth = self.__columnWidth
      self.rowOffset = self.__rowOffset

      return OsReturn.ok

class MetrologyReportParser(object):

   def __init__(self, iDesc):
      self.iDesc = iDesc

   def __getTokensAsStringFromString(self, fname, tokens, reportStr):

      outStr = []

      strLines = reportStr.splitlines()

      for token in tokens:
         retVal = token.find(fname, strLines)

         if retVal != OsReturn.ok:
            return retVal, ""

         startOffset = token.columnOffset
         endOffset = startOffset + token.columnWidth

         outStr.append(
            strLines[token.rowOffset][startOffset:endOffset] + ", ")

      return OsReturn.ok, outStr

   def getTokensAsString(self, tokens):
      retVal = []
      retStr = []

      retVal, fname, reportStr = self.iDesc.read()

      if retVal == IoDesc.fileError:
         return OsReturn.error, []

      while retVal == IoDesc.ok:
         retVal, outStr = self.__getTokensAsStringFromString(
            fname, tokens, reportStr)

         if retVal != OsReturn.ok:
            return retVal, []

         # Add filename to the beginning of the list
         outStr.insert(0, fname + ", ")

         # Add newline after all tokens
         outStr.append(os.linesep)

         retStr += outStr

         retVal, fname, reportStr = self.iDesc.read()


      if retVal == IoDesc.fileError:
         return OsReturn.error, []
      else:
         return OsReturn.ok, retStr

class ArgParser:
   ok = 0
   endProgram = 1
   
   programName = ""
   inFileNames = []
   outFileName = ""

   def __init__(self, programName):
      self.programName = programName

   def parse(self, argv):
      try:
         opts, args = getopt.getopt(argv, 'h', ["help", "file="])
      except getopt.GetoptError, err:
         print(str(err) + " (\"" + self.programName + " -h\" for help)")
         return self.endProgram

      if len(argv) == 0:
         print("No parameters provided (\"" + self.programName + 
               " -h\" for help)")
         return self.endProgram

      for opt, arg in opts:
         if opt in ("-h", "--help"):
            self.usage()
            return self.endProgram
         elif opt in ("--file"):
            self.outFileName = arg

      self.inFileNames += argv[len(opts):]

      return self.ok

   def usage(self):
      pn = self.programName
      print(
"===============================================================================\n"
"Name:\n"
"  " + pn + " - compiles metrology text reports into CSV\n"
"===============================================================================\n"
"Synopsis:\n"
"  " + pn + " [OPTION]... [input_file]...\n"
"===============================================================================\n"
"Description:\n"
"  This tool parses ascii metrology report(s) and outputs CSV with key\n"
"  information from the report(s)\n"
"===============================================================================\n"
"Options:\n"
"  --help (-h)     Prints this help.\n"
"  --file          The name of the output file.  If no file is given output\n"
"                  goes to stdout.\n"
"==============================================================================\n"
"Examples:\n"
"  " + pn + " --help\n"
"    Prints this help message\n"
"  " + pn + " -h\n"
"    Prints this help message\n"
"  " + pn + " report.txt\n"
"    Processes report.txt and outputs CSV to stdout\n"
"  " + pn + " --file out.txt report.txt\n"
"    Processes report.txt and outputs CSV to out.txt, clobbering out.txt if \n"
"    it exists\n"
"=============================================================================="
      )
      


def main(args):
   argInfo = ArgParser(args[0])
   retVal = argInfo.parse(args[1:])

   if retVal == ArgParser.endProgram:
      return OsReturn.ok

   iDesc = IDesc(argInfo.inFileNames)

   pin1Token = MetrologyReportToken("pin1 nominal value", 26, 9, 17)
   pin2Token = MetrologyReportToken("pin2 nominal value", 26, 9, 14)
   pin3Token = MetrologyReportToken("pin3 nominal value", 26, 9, 23)
   pin4Token = MetrologyReportToken("pin4 nominal value", 26, 9, 20)
   allTokens = [pin1Token, pin2Token, pin3Token, pin4Token]

   mrParser = MetrologyReportParser(iDesc)

   retVal, tokenString = mrParser.getTokensAsString(allTokens)

   if retVal != OsReturn.ok:
      return retVal

   oDesc = ODesc(argInfo.outFileName)

   for itemStr in tokenString:
      oDesc.write(itemStr)

   return OsReturn.ok

if __name__ == "__main__":
   exit(main(sys.argv))
