using System;
using System.Runtime.InteropServices;

public class FormTest {
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
    public struct FORM_INFO_1 {
        public int Flags;
        public string pName;
        public int SizeWidth;
        public int SizeHeight;
        public int ImageableAreaLeft;
        public int ImageableAreaTop;
        public int ImageableAreaRight;
        public int ImageableAreaBottom;
    }

    [DllImport("winspool.drv", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern bool OpenPrinter(string pPrinterName, out IntPtr phPrinter, IntPtr pDefault);

    [DllImport("winspool.drv", SetLastError = true)]
    public static extern bool ClosePrinter(IntPtr hPrinter);

    [DllImport("winspool.drv", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern bool AddForm(IntPtr hPrinter, int Level, ref FORM_INFO_1 pForm);

    public static int Main() {
        IntPtr hPrinter;
        if (OpenPrinter("EPSON M105 Series", out hPrinter, IntPtr.Zero)) {
            FORM_INFO_1 form = new FORM_INFO_1();
            form.Flags = 0; // USER form
            form.pName = "RibbonTempForm";
            // 1 mm = 1000 thousandths of a mm
            form.SizeWidth = 38000;
            form.SizeHeight = 400000;
            form.ImageableAreaLeft = 0;
            form.ImageableAreaTop = 0;
            form.ImageableAreaRight = 38000;
            form.ImageableAreaBottom = 400000;

            if (AddForm(hPrinter, 1, ref form)) {
                Console.WriteLine("Form Added Successfully!");
            } else {
                Console.WriteLine("AddForm failed. Error: " + Marshal.GetLastWin32Error());
            }
            ClosePrinter(hPrinter);
            return 0;
        }
        Console.WriteLine("OpenPrinter failed.");
        return 1;
    }
}
