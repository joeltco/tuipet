/*
 * Decompiled with CFR 0.152.
 */
package Controller;

import Controller.ClockTic;
import Controller.JogressProtocol;
import Controller.Utility;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.InetSocketAddress;
import java.net.Socket;

public class JogressConnect
extends JogressProtocol {
    private Socket _clientSocket;
    private InetSocketAddress _socketAddress;

    public Socket getClientSocket() {
        return this._clientSocket;
    }

    public InetSocketAddress getSocketAddress() {
        return this._socketAddress;
    }

    public JogressConnect(ClockTic controller, String hostName, String jogressMatch) {
        super(controller, jogressMatch);
        this._socketAddress = Utility.getSocketAddress(hostName);
    }

    private void attemptConnection() {
        try {
            boolean jogressStart = false;
            this._input = new BufferedReader(new InputStreamReader(this._clientSocket.getInputStream()));
            this._output = new BufferedWriter(new OutputStreamWriter(this._clientSocket.getOutputStream()));
            try {
                this._clientSocket.setSoTimeout(5000);
                String uniqueStart = "";
                uniqueStart = this._input.readLine();
                if (uniqueStart.equals("Jogress Start")) {
                    jogressStart = true;
                } else {
                    System.out.println("Issue in jogress start jogressconnect");
                    this._controller.onError(false);
                }
            }
            catch (Exception exc) {
                System.out.println(exc.getMessage() + ": Issue in battle connect when attempting connection.");
                if (this._controller != null) {
                    this._controller.onError(false);
                }
                exc.printStackTrace();
            }
            if (jogressStart) {
                super.receivePartnerInfo(this._input);
                super.sendPlayerInfo(this._output);
                if (super.jogressFindFusionsAndAttributes()) {
                    this._jogressMatch = this._input.readLine();
                }
                super.checkJogress();
            }
        }
        catch (Exception e) {
            System.out.println(e.getMessage() + ": Issue attempting connection.");
            if (this._controller != null) {
                this._controller.onError(false);
            }
            e.printStackTrace();
        }
    }

    public void checkJogressStart() {
        try {
            if (this._clientSocket != null && this._clientSocket.isConnected()) {
                this.attemptConnection();
            } else {
                this._clientSocket = new Socket();
                this._clientSocket.connect(this._socketAddress);
                if (this._clientSocket != null && this._clientSocket.isConnected()) {
                    this.attemptConnection();
                }
            }
        }
        catch (Exception e) {
            System.out.println(e.getMessage() + ": Issue communicating with server.");
            if (this._controller != null) {
                this._controller.onError(false);
            }
            e.printStackTrace();
        }
    }

    @Override
    public void dispose() {
        try {
            if (this._clientSocket != null) {
                this._clientSocket.close();
            }
        }
        catch (IOException iOException) {
            // empty catch block
        }
        this._clientSocket = null;
        this._socketAddress = null;
        super.dispose();
    }
}

