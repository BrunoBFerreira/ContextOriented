import pythoncom
from win32com.shell import shell,shellcon

def win_copy_files(src_files,dst_folder):
    # @see IFileOperation
    pfo = pythoncom.CoCreateInstance(shell.CLSID_FileOperation,None,pythoncom.CLSCTX_ALL,shell.IID_IFileOperation)
    # Respond with Yes to All for any dialog
    # @see http://msdn.microsoft.com/en-us/library/bb775799(v=vs.85).aspx
    pfo.SetOperationFlags(shellcon.FOF_NOCONFIRMATION)

    # Set the destionation folder
    dst = shell.SHCreateItemFromParsingName(dst_folder,None,shell.IID_IShellItem)
    for f in src_files:
        src = shell.SHCreateItemFromParsingName(f,None,shell.IID_IShellItem)
        pfo.CopyItem(src,dst) # Schedule an operation to be performed
        # @see http://msdn.microsoft.com/en-us/library/bb775780(v=vs.85).aspx
        success = pfo.PerformOperations()
        # @see sdn.microsoft.com/en-us/library/bb775769(v=vs.85).aspx
        aborted = pfo.GetAnyOperationsAborted()
        return success and not aborted

#files_to_copy = [r'C:\Users\jrm\Documents\test1.txt',r'C:\Users\jrm\Documents\test2.txt']
#dest_folder = r'C:\Users\jrm\Documents\dst'
#win_copy_files(files_to_copy,dest_folder)