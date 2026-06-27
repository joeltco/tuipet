/*
 * Decompiled with CFR 0.152.
 */
package Controller;

import Model.Config;
import Model.Enum;
import Model.ShopConsumable;
import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.InetSocketAddress;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Random;

public class Utility {
    public static final Enum.State[] ENABLE_DURING_STATE = new Enum.State[]{Enum.State.Idling, Enum.State.PoopDance, Enum.State.Yawning, Enum.State.Weathering, Enum.State.Surprising, Enum.State.Personality_Angry, Enum.State.Personality_Happy, Enum.State.Tantrum};
    public static final Enum.State[] DISABLE_RAIN_DURING_STATE = new Enum.State[]{Enum.State.Attack_Contact, Enum.State.HealthInc, Enum.State.PerfectWinsInc, Enum.State.ZoneChange, Enum.State.WhaTransportSwim, Enum.State.Tourney_Start, Enum.State.BossParade, Enum.State.UnlockDNA, Enum.State.UnlockFood, Enum.State.UnlockInheritance, Enum.State.UnlockItem, Enum.State.EvolSilhouetteBack, Enum.State.EvolSilhouetteTransition, Enum.State.Buying_Food, Enum.State.Buying_Habitat, Enum.State.Buying_Item, Enum.State.Selling_Item, Enum.State.Selling_Food, Enum.State.EarningBits, Enum.State.Virus_Training, Enum.State.MapComplete, Enum.State.Vaccine_Training, Enum.State.Battle_Flash, Enum.State.Jogress_Flash, Enum.State.EarningBits_Tourney, Enum.State.DNA_Generate};
    public static final Enum.State[] ASSISTANT_ANIM = new Enum.State[]{Enum.State.Assistant_Clean, Enum.State.Assistant_Feed, Enum.State.Assistant_Lights};
    public static final Enum.State[] DISABLE_CLOCK_SPEED_CHANGE = new Enum.State[]{Enum.State.TournamentAlert, Enum.State.GiftCall, Enum.State.DiscoverCall, Enum.State.BossParade, Enum.State.Dying, Enum.State.UnlockDNA, Enum.State.UnlockFood, Enum.State.UnlockItem, Enum.State.UnlockInheritance, Enum.State.Vaccine_Training, Enum.State.Data_Training, Enum.State.Virus_Training, Enum.State.HP_Training, Enum.State.HP_Training_AttackFail, Enum.State.HP_Training_AttackSuccess, Enum.State.DNA_Generate, Enum.State.Hatching, Enum.State.Evolving, Enum.State.Jogress, Enum.State.Battle_Flash, Enum.State.Jogress_Flash};

    public static String getExistingFileLoc(String firstLoc, String secondLoc, String fileName) {
        if (!fileName.isEmpty()) {
            File f = new File(firstLoc + fileName);
            if (f.exists()) {
                return firstLoc + fileName;
            }
            return secondLoc + fileName;
        }
        return "";
    }

    public static InputStream getInputStream(String MOD_FOLDER, String RESOURCES_FOLDER, String fileName) {
        String path = Utility.getExistingFileLoc(MOD_FOLDER, RESOURCES_FOLDER, fileName);
        InputStream is = null;
        try {
            if (!fileName.isEmpty() && !path.isEmpty()) {
                is = path.contains(MOD_FOLDER) ? Files.newInputStream(Paths.get(path, new String[0]), new OpenOption[0]) : Utility.class.getResourceAsStream(path);
            }
        }
        catch (IOException ex) {
            ex.printStackTrace();
        }
        return is;
    }

    public static String createCSVString(String[] info) {
        String csv = "";
        for (String s : info) {
            csv = csv + s + ",";
        }
        return csv;
    }

    public static String changeCSVEntry(int i, String entry, String[] csv) {
        String result = "";
        csv[i] = entry;
        return Utility.createCSVString(csv);
    }

    public static boolean isBlank(String s) {
        return s == null || s.trim().equals("");
    }

    public static boolean isEmpty(String s) {
        return s.equals("");
    }

    public static boolean containsState(Enum.State[] states, Enum.State state) {
        boolean contains = false;
        for (Enum.State s : states) {
            if (s != state) continue;
            contains = true;
            break;
        }
        return contains;
    }

    public static boolean containsState(Enum.State[] states, ArrayList<Enum.State> state) {
        boolean contains = false;
        for (Enum.State s : states) {
            if (!state.contains((Object)s)) continue;
            return true;
        }
        return contains;
    }

    public static boolean randomChance(int target, int bound) {
        Random rand;
        int ran;
        if (bound <= 0) {
            bound = 1;
        }
        return (ran = (rand = new Random()).nextInt(bound)) < target;
    }

    public static int randomBetween(int min, int max) {
        Random r = new Random();
        int range = max - min + 1;
        return r.nextInt(range <= 0 ? 1 : range) + min;
    }

    public static int calcVariance(double coefficient, double value) {
        double variance = value * coefficient;
        return Utility.randomBetween((int)(value - variance), (int)(value + variance));
    }

    public static boolean[] binaryStringToBooleanArray(int b) {
        String s1 = String.format("%8s", Integer.toBinaryString(b & 0xFF)).replace(' ', '0');
        char[] binary = s1.toCharArray();
        boolean[] bool = new boolean[binary.length];
        for (int i = 0; i < bool.length; ++i) {
            bool[i] = binary[binary.length - 1 - i] == '1';
        }
        return bool;
    }

    /*
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    public static String[] getCSVRecord(InputStream in, int record) {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(in, "utf-8"));){
            String line = reader.readLine();
            int index = 0;
            while ((line = reader.readLine()) != null) {
                if (index == record) {
                    String[] stringArray = line.split(",");
                    return stringArray;
                }
                ++index;
            }
            in.close();
            return null;
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public static boolean isOpen(int h, byte[] time) {
        return h >= time[0] && h <= time[1];
    }

    public static InetSocketAddress getSocketAddress(String hostName) {
        String[] host = hostName.split(":");
        return new InetSocketAddress(host[0], host.length > 1 ? Integer.valueOf(host[1]) : Config._portNum);
    }

    public static int maxValue(int[] array) {
        int max = Arrays.stream(array).max().getAsInt();
        return max;
    }

    public static ArrayList<ShopConsumable> getConsumableID(String[] data, ArrayList<ShopConsumable> c) {
        ArrayList<ShopConsumable> list = new ArrayList<ShopConsumable>();
        if (data.length > 0) {
            for (String s : data) {
                list.add(c.get(Integer.parseInt(s)));
            }
        }
        return list;
    }
}

