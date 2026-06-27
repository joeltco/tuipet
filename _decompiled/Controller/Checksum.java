/*
 * Decompiled with CFR 0.152.
 */
package Controller;

import Model.CrashEntry;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.net.URISyntaxException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

public class Checksum {
    public static String generate() {
        File currentJavaJarFile = null;
        try {
            currentJavaJarFile = new File(Checksum.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        }
        catch (URISyntaxException ex) {
            ex.printStackTrace();
        }
        String filepath = currentJavaJarFile.getAbsolutePath();
        StringBuilder sb = new StringBuilder();
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            FileInputStream fis = new FileInputStream(filepath);
            byte[] dataBytes = new byte[1024];
            int nread = 0;
            while ((nread = fis.read(dataBytes)) != -1) {
                md.update(dataBytes, 0, nread);
            }
            byte[] mdbytes = md.digest();
            for (int i = 0; i < mdbytes.length; ++i) {
                sb.append(Integer.toString((mdbytes[i] & 0xFF) + 256, 16).substring(1));
            }
            return sb.toString();
        }
        catch (IOException | NoSuchAlgorithmException e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
            return "";
        }
    }
}

