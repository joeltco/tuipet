/*
 * Decompiled with CFR 0.152.
 */
package Model;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.logging.Level;
import java.util.logging.Logger;

public class CrashEntry {
    public static void generateEntry(Throwable e) {
        String filename = "files" + File.separator + "errorlogs.txt";
        File log = new File(filename);
        if (!log.exists() || log.exists() && log.length() >= 1000000L) {
            if (log.exists()) {
                log.delete();
            }
            try {
                FileWriter newFile = new FileWriter(filename);
                newFile.close();
            }
            catch (IOException ex) {
                Logger.getLogger(CrashEntry.class.getName()).log(Level.SEVERE, null, ex);
            }
        }
        if (log.exists()) {
            Calendar cal = Calendar.getInstance();
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy_MM_dd HH:mm:ss");
            String entry = sdf.format(cal.getTime()) + " : " + e.getClass() + " : " + e.getMessage();
            try (BufferedWriter save = new BufferedWriter(new FileWriter(filename, true));){
                save.newLine();
                save.write(entry);
                save.newLine();
                for (int i = 0; i < e.getStackTrace().length; ++i) {
                    save.write(e.getStackTrace()[i].toString());
                    save.newLine();
                }
            }
            catch (IOException exc) {
                exc.printStackTrace();
            }
        }
    }

    public static void generateEntry(String s) {
        String filename = "files" + File.separator + "errorlogs.txt";
        File log = new File(filename);
        if (!log.exists() || log.exists() && log.length() >= 1000000L) {
            if (log.exists()) {
                log.delete();
            }
            try {
                FileWriter newFile = new FileWriter(filename);
                newFile.close();
            }
            catch (IOException ex) {
                Logger.getLogger(CrashEntry.class.getName()).log(Level.SEVERE, null, ex);
            }
        }
        if (log.exists()) {
            Calendar cal = Calendar.getInstance();
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy_MM_dd HH:mm:ss");
            String entry = sdf.format(cal.getTime()) + " : CustomMessage";
            try (BufferedWriter save = new BufferedWriter(new FileWriter(filename, true));){
                save.newLine();
                save.write(entry);
                save.newLine();
                save.write(s);
                save.newLine();
            }
            catch (IOException exc) {
                exc.printStackTrace();
            }
        }
    }
}

