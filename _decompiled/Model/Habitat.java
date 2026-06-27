/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.Enum;
import java.util.ArrayList;

public class Habitat {
    private int _id;
    private String _fileName = "defaultBack.png";
    private byte[] _springTemp = new byte[]{20, 60};
    private byte[] _summerTemp = new byte[]{60, 100};
    private byte[] _fallTemp = new byte[]{20, 60};
    private byte[] _winterTemp = new byte[]{0, 40};
    private byte _springMod = (byte)10;
    private byte _summerMod = 0;
    private byte _fallMod = (byte)10;
    private byte _winterMod = (byte)20;
    private byte _cloudMod = (byte)10;
    private int _weatherChance = 250;
    private int _weatherChange = 100;
    public byte[] _springTime = new byte[3];
    public byte[] _summerTime = new byte[3];
    public byte[] _fallTime = new byte[3];
    public byte[] _winterTime = new byte[3];
    public ArrayList<Enum.Field> _compatibleFields = new ArrayList();
    public ArrayList<Enum.Element> _compatibleElements = new ArrayList();
    public ArrayList<Enum.Field> _incompatibleFields = new ArrayList();
    public ArrayList<Enum.Element> _incompatibleElements = new ArrayList();
    private int _price = 0;
    private boolean _unlocked;
    private String _description;
    private String _name;
    private int _nightTempFactor;
    private int _morningTempFactor;

    public int getID() {
        return this._id;
    }

    public String getFileName() {
        return this._fileName;
    }

    public byte[] getSpringTemp() {
        return this._springTemp;
    }

    public byte[] getSummerTemp() {
        return this._summerTemp;
    }

    public byte[] getFallTemp() {
        return this._fallTemp;
    }

    public byte[] getWinterTemp() {
        return this._winterTemp;
    }

    public byte getSpringMod() {
        return this._springMod;
    }

    public byte getSummerMod() {
        return this._summerMod;
    }

    public byte getFallMod() {
        return this._fallMod;
    }

    public byte getWinterMod() {
        return this._winterMod;
    }

    public byte getCloudMod() {
        return this._cloudMod;
    }

    public int getWeatherChance() {
        return this._weatherChance;
    }

    public int getWeatherChange() {
        return this._weatherChange;
    }

    public byte[] getSpringTime() {
        return this._springTime;
    }

    public byte[] getSummerTime() {
        return this._summerTime;
    }

    public byte[] getFallTime() {
        return this._fallTime;
    }

    public byte[] getWinterTime() {
        return this._winterTime;
    }

    public int getPrice() {
        return this._price;
    }

    public boolean getUnlocked() {
        return this._unlocked;
    }

    public void setUnlocked(boolean unlocked) {
        this._unlocked = unlocked;
    }

    public String getDescription() {
        return this._description;
    }

    public String getName() {
        return this._name;
    }

    public ArrayList<Enum.Field> getCompatibleFields() {
        return this._compatibleFields;
    }

    public ArrayList<Enum.Element> getCompatibleElements() {
        return this._compatibleElements;
    }

    public ArrayList<Enum.Field> getIncompatibleFields() {
        return this._incompatibleFields;
    }

    public ArrayList<Enum.Element> getIncompatibleElements() {
        return this._incompatibleElements;
    }

    public int getNightTempFactor() {
        return this._nightTempFactor;
    }

    public int getMorningTempFactor() {
        return this._morningTempFactor;
    }

    public Habitat() {
    }

    public Habitat(String[] info) {
        int i;
        this._id = Integer.parseInt(info[0]);
        this._fileName = info[1] + ".png";
        String[] range = info[2].split("t");
        this._springTemp[0] = Byte.parseByte(range[0]);
        this._springTemp[1] = Byte.parseByte(range[1]);
        range = info[3].split("t");
        this._summerTemp[0] = Byte.parseByte(range[0]);
        this._summerTemp[1] = Byte.parseByte(range[1]);
        range = info[4].split("t");
        this._fallTemp[0] = Byte.parseByte(range[0]);
        this._fallTemp[1] = Byte.parseByte(range[1]);
        range = info[5].split("t");
        this._winterTemp[0] = Byte.parseByte(range[0]);
        this._winterTemp[1] = Byte.parseByte(range[1]);
        this._springMod = Byte.parseByte(info[6]);
        this._summerMod = Byte.parseByte(info[7]);
        this._fallMod = Byte.parseByte(info[8]);
        this._winterMod = Byte.parseByte(info[9]);
        this._cloudMod = Byte.parseByte(info[10]);
        this._weatherChance = Integer.parseInt(info[11]);
        this._weatherChange = Integer.parseInt(info[12]);
        this._price = Integer.parseInt(info[13]);
        this._unlocked = Boolean.parseBoolean(info[14]);
        this._description = info[15];
        this._name = info[16];
        range = info[17].split(";");
        for (i = 0; i < range.length; ++i) {
            this._springTime[i] = Byte.parseByte(range[i]);
        }
        range = info[18].split(";");
        for (i = 0; i < range.length; ++i) {
            this._summerTime[i] = Byte.parseByte(range[i]);
        }
        range = info[19].split(";");
        for (i = 0; i < range.length; ++i) {
            this._fallTime[i] = Byte.parseByte(range[i]);
        }
        range = info[20].split(";");
        for (i = 0; i < range.length; ++i) {
            this._winterTime[i] = Byte.parseByte(range[i]);
        }
        range = info[21].split(";");
        for (i = 0; i < range.length; ++i) {
            if (range[i].isEmpty()) continue;
            try {
                this._compatibleFields.add(Enum.Field.valueOf(range[i]));
                continue;
            }
            catch (IllegalArgumentException illegalArgumentException) {
                // empty catch block
            }
        }
        range = info[22].split(";");
        for (i = 0; i < range.length; ++i) {
            if (range[i].isEmpty()) continue;
            try {
                this._compatibleElements.add(Enum.Element.valueOf(range[i]));
                continue;
            }
            catch (IllegalArgumentException illegalArgumentException) {
                // empty catch block
            }
        }
        range = info[23].split(";");
        for (i = 0; i < range.length; ++i) {
            if (range[i].isEmpty()) continue;
            try {
                this._incompatibleFields.add(Enum.Field.valueOf(range[i]));
                continue;
            }
            catch (IllegalArgumentException illegalArgumentException) {
                // empty catch block
            }
        }
        range = info[24].split(";");
        for (i = 0; i < range.length; ++i) {
            if (range[i].isEmpty()) continue;
            try {
                this._incompatibleElements.add(Enum.Element.valueOf(range[i]));
                continue;
            }
            catch (IllegalArgumentException illegalArgumentException) {
                // empty catch block
            }
        }
        this._nightTempFactor = Integer.parseInt(info[25]);
        this._morningTempFactor = Integer.parseInt(info[26]);
    }
}

