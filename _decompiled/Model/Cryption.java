/*
 * Decompiled with CFR 0.152.
 */
package Model;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.io.PrintWriter;
import java.io.UnsupportedEncodingException;
import java.security.InvalidKeyException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import javax.crypto.BadPaddingException;
import javax.crypto.Cipher;
import javax.crypto.IllegalBlockSizeException;
import javax.crypto.NoSuchPaddingException;
import javax.crypto.SecretKey;
import javax.crypto.spec.SecretKeySpec;

public class Cryption {
    private static final String CIPHER = "AES/ECB/PKCS5Padding";

    public static ArrayList<String> encrypt(String key, String inputFile) {
        return Cryption.processFile(true, key, inputFile);
    }

    public static ArrayList<String> decrypt(String key, String inputFile) {
        return Cryption.processFile(false, key, inputFile);
    }

    private static SecretKey initKey(String myKey) {
        MessageDigest sha = null;
        byte[] key = null;
        try {
            key = myKey.getBytes("UTF-8");
            sha = MessageDigest.getInstance("SHA-1");
            key = sha.digest(key);
            key = Arrays.copyOf(key, 16);
            return new SecretKeySpec(key, "AES");
        }
        catch (UnsupportedEncodingException | NoSuchAlgorithmException e) {
            e.printStackTrace();
            return null;
        }
    }

    private static ArrayList<String> processFile(boolean doEncrypt, String key, String inputFile) {
        ArrayList<String> lines = new ArrayList<String>();
        SecretKey sKey = Cryption.initKey(key);
        Cipher cipher = null;
        try {
            block24: {
                cipher = Cipher.getInstance(CIPHER);
                try (FileReader in = new FileReader(inputFile);
                     BufferedReader reader = new BufferedReader(in);){
                    String line;
                    while ((line = reader.readLine()) != null) {
                        if (doEncrypt) {
                            lines.add(Cryption.doEncrypt(cipher, sKey, line));
                            continue;
                        }
                        lines.add(Cryption.doDecrypt(cipher, sKey, line));
                    }
                    if (!doEncrypt) break block24;
                    try (PrintWriter save = new PrintWriter(inputFile);){
                        for (String s : lines) {
                            save.println(s);
                        }
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                }
                catch (IOException ex) {
                    ex.printStackTrace();
                }
            }
            return lines;
        }
        catch (NoSuchAlgorithmException | NoSuchPaddingException ex) {
            ex.printStackTrace();
            return null;
        }
    }

    private static String doEncrypt(Cipher cipher, SecretKey sKey, String line) {
        try {
            cipher.init(1, sKey);
            return Base64.getEncoder().encodeToString(cipher.doFinal(line.getBytes("UTF-8")));
        }
        catch (UnsupportedEncodingException | InvalidKeyException | BadPaddingException | IllegalBlockSizeException ex) {
            ex.printStackTrace();
            return line;
        }
    }

    private static String doDecrypt(Cipher cipher, SecretKey sKey, String line) {
        try {
            cipher.init(2, sKey);
            return new String(cipher.doFinal(Base64.getDecoder().decode(line)));
        }
        catch (InvalidKeyException | BadPaddingException | IllegalBlockSizeException ex) {
            ex.printStackTrace();
            return line;
        }
    }
}

