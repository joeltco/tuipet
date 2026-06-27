/*
 * Decompiled with CFR 0.152.
 */
package Controller;

import Controller.ClockTic;
import Model.Enemy;
import Model.Enum;
import Model.EvolutionInfo;
import Model.PhysicalState;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.net.ServerSocket;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;

public class JogressProtocol {
    protected ClockTic _controller;
    public final String JOGRESS_START = "Jogress Start";
    public BufferedReader _input;
    public BufferedWriter _output;
    protected boolean _isConnection;
    protected Enemy _partner;
    protected int _playerIndex;
    protected int _partnerIndex = -1;
    protected String _jogressMatch;
    protected ServerSocket _serverSocket;

    public String getJogressMatch() {
        return this._jogressMatch;
    }

    public int getPartnerIndex() {
        return this._partnerIndex;
    }

    public JogressProtocol(ClockTic controller, String jogressMatch) {
        this._jogressMatch = jogressMatch;
        this._controller = controller;
        this._playerIndex = this._controller.getModel().getDigimon().getIndex();
    }

    public boolean jogressFindFusionsAndAttributes() throws IOException {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        Map<String, ArrayList<String>> partner = this.getAttributesAndFusions(this._input.readLine().split(","));
        Map<String, ArrayList<String>> jogresses = this.getAttributesAndFusions(this._jogressMatch.split(","));
        ArrayList<String> matches = new ArrayList<String>();
        for (String string : partner.get("fusions")) {
            if (string.equals("") || !jogresses.get("fusions").contains(string)) continue;
            matches.add(string);
        }
        if (!matches.isEmpty()) {
            ArrayList<EvolutionInfo> e = new ArrayList<EvolutionInfo>();
            for (String string : matches) {
                e.addAll(digimon.getEvolution().getDigimonList(string));
            }
            ArrayList<EvolutionInfo> arrayList = digimon.getEvolution().getFinalEvolution(e, digimon);
            Random random = new Random();
            this._jogressMatch = arrayList.get(random.nextInt(arrayList.size())).getName();
            return true;
        }
        this._jogressMatch = this._partner.getOppStage().equals((Object)digimon.getGrowthStage()) && partner.get("attributes").contains(digimon.getAttribute().toString()) && jogresses.get("attributes").contains(this._partner.getOppAttribute().toString()) ? this._partner.getOppAttribute().toString() : "";
        return false;
    }

    public void checkJogress() {
        if (this._playerIndex == this._partnerIndex) {
            this._jogressMatch = "";
        }
        this._controller.getView().setFrame(-1);
        this._controller.startJogress(this._jogressMatch, this._partner.getIsSick());
    }

    public void setupServerSocket(int port) {
        try {
            this._serverSocket = new ServerSocket(port);
        }
        catch (Exception e) {
            if (this._controller != null) {
                this._controller.onError(false);
            }
            e.printStackTrace();
        }
    }

    public void receivePartnerInfo(BufferedReader input) {
        int[] partner = new int[3];
        boolean isSick = false;
        try {
            partner[0] = Integer.parseInt(input.readLine());
            partner[1] = Integer.parseInt(input.readLine());
            partner[2] = Integer.parseInt(input.readLine());
            this._partnerIndex = Integer.parseInt(input.readLine());
            isSick = Boolean.parseBoolean(input.readLine());
            Enum.Attribute a = Enum.Attribute.valueOf(input.readLine());
            this._partner = new Enemy();
            this._partner.setSpriteNum(partner[0]);
            this._partner.setSpriteSet(partner[1]);
            this._partner.setOppStage(Enum.Stage.values()[partner[2]]);
            this._partner.setIsSick(isSick);
            this._partner.setOppAttribute(a);
            this._controller.setJogressPartner(this._partner);
        }
        catch (Exception e) {
            if (this._controller != null) {
                this._controller.onError(false);
            }
            e.printStackTrace();
        }
    }

    public void sendPlayerInfo(BufferedWriter output) {
        PhysicalState digimon = this._controller.getModel().getDigimon();
        try {
            output.write(Integer.toString(digimon.getSpriteNum()));
            output.newLine();
            output.write(Integer.toString(digimon.getSpriteSet()));
            output.newLine();
            output.write(Integer.toString(digimon.getGrowthStage().ordinal()));
            output.newLine();
            output.write(Integer.toString(this._playerIndex));
            output.newLine();
            output.write(Boolean.toString(digimon.isSick()));
            output.newLine();
            output.write(digimon.getAttribute().toString());
            output.newLine();
            output.write(this._controller.getView().getJogressMatch());
            output.newLine();
            output.flush();
        }
        catch (Exception e) {
            if (this._controller != null) {
                this._controller.onError(false);
            }
            e.printStackTrace();
        }
    }

    public Map<String, ArrayList<String>> getAttributesAndFusions(String[] info) {
        ArrayList<String> attributes = new ArrayList<String>();
        ArrayList<String> fusions = new ArrayList<String>();
        for (String s : info) {
            try {
                Enum.Attribute a = Enum.Attribute.valueOf(s);
                attributes.add(s);
            }
            catch (IllegalArgumentException e) {
                fusions.add(s);
            }
        }
        HashMap<String, ArrayList<String>> map = new HashMap<String, ArrayList<String>>();
        map.put("attributes", attributes);
        map.put("fusions", fusions);
        return map;
    }

    public void dispose() {
        try {
            if (this._input != null) {
                this._input.close();
            }
            if (this._output != null) {
                this._output.close();
            }
            if (this._serverSocket != null) {
                this._serverSocket.close();
            }
        }
        catch (IOException iOException) {
            // empty catch block
        }
        this._controller = null;
        this._input = null;
        this._output = null;
        this._partner = null;
        this._jogressMatch = null;
        this._serverSocket = null;
    }
}

