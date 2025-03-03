import argparse
import ROOT
import numpy as np
from array import array
from pathlib import Path   
import os
import math
from datetime import datetime, timezone, timedelta

class Event:
	fTime = 0.
	fNpe = 0.

class BiPo:
	fTime = 0.
	fDT = 0.
	fEBi = 0.
	fEPo = 0.

class AnalysisManager():
	
	fRunPath = ""
	fOutDir = None
	fStepTime = 1. #seconds
	fEBiMin = 1.
	fEBiMax = 1.
	fEPoMin = 1.
	fEPoMax = 1.
	fDelayMax = 1. #second
	fMuEVeto = 1.
	fMuTimeVeto = 1. #second
	fEfficiency = 1.
	fVolumeI = 1.
	fVolumeF = 1.
	fVolumeFile = ""

	fRunTime = 0.

	fSavePlot = False
	fSaveRoot = False

	def GetVolume(self, t):
			return self.fVolumeI + (self.fVolumeF-self.fVolumeI)/self.fRunTime*t
	
	def ProcessIt(self):
		
		tFile = ROOT.TFile(self.fRunPath, "READ")
		tree = tFile.Get("CdEvents")

		events = []
		BiPoList = []
		nCoinc = 0

		path = Path(self.fRunPath)
		runName = path.name.removesuffix(".root")

		if (self.fOutDir) :
			if not os.path.exists(self.fOutDir):
				os.makedirs(self.fOutDir)
			resultsFile = open(self.fOutDir+"/"+path.name.removesuffix(".root") + ".txt" , "w")
		else :
			if not os.path.exists(runName):
				os.makedirs(runName)
			resultsFile = open(runName+"/"+path.name.removesuffix(".root") + ".txt" , "w")
		
		runStartTime = 0
		for event in tree:
			runStartTime = event.TimeStamp.GetSec()
			break

		for i, event in enumerate(tree):
			if(i%1000000==0): print("Read events: " + str(i))
			if(event.TriggerType != "Periodic") :
				evt = Event()
				evt.fTime = (float(event.TimeStamp.GetSec()-runStartTime))+(float(event.TimeStamp.GetNanoSec())/1e9)
				evt.fNpe = event.npe
				events.append(evt)
			#if(len(events)>1000): break #use for debug to reduce import time

		timeSkip = 0
		muonCount = 0
		for i in range(len(events)):
			#Muon veto
			if(events[i].fNpe > self.fMuEVeto):
				timeSkip = events[i].fTime
				muonCount+=1
			if(timeSkip>0):
				if(events[i].fTime < timeSkip + self.fMuTimeVeto):
					continue
			else:
				timeSkip=0
			#BiPo coincidence
			if(self.fEPoMin < events[i].fNpe < self.fEPoMax):
				j=i-1
				while(events[j].fTime > events[i].fTime - self.fDelayMax and j > 0):
					if(self.fEBiMin < events[j].fNpe < self.fEBiMax):
						bipo = BiPo()
						bipo.fTime = events[j].fTime
						bipo.fDT = events[i].fTime - events[j].fTime
						bipo.fEBi = events[j].fNpe
						bipo.fEPo = events[i].fNpe
						BiPoList.append(bipo)
						nCoinc+=1
					j-=1

		canvas = ROOT.TCanvas("c1")
		canvas.SetLogy()

		histoDT = ROOT.TH1F("DT", "", 100, 0, self.fDelayMax)
		histoAux = ROOT.TH1F("Energy spetra", "", 10, self.fEPoMin, self.fEBiMax)
		histoEBi = ROOT.TH1F("istoEBi", "", 100, self.fEBiMin, self.fEBiMax)
		histoEPo = ROOT.TH1F("istoEPo", "", 100, self.fEPoMin, self.fEPoMax)
		histoEBi.SetLineColor(1)
		histoEPo.SetLineColor(2)

		startTime = events[0].fTime
		stopTime = events[-1].fTime
		self.fRunTime = stopTime - startTime
		runStopTime = runStartTime + self.fRunTime
		runDTPerc = 100*muonCount*self.fMuTimeVeto / self.fRunTime
		print("Number of all Bi-Po candidates: ", nCoinc)
		print("Run time (s): %.1f"%(self.fRunTime))
		print("Dead time (%%): %.1e"%(runDTPerc))

		resultsFile.write("Run number: " + runName + "\n")
		resultsFile.write("File path: " + self.fRunPath + "\n")
		resultsFile.write("Total run time (s): %.1f\n"%(self.fRunTime))
		resultsFile.write("Mean dead time (%%): %.1e\n"%(runDTPerc))
		resultsFile.write("Date\tTime\tDuration\tSignal\tErrSignal\tBkg\tErrBkg\tChi2Rid\tActivity\tErrActivity\n")

		#Read volume file if available
		
		if(self.fVolumeFile != ""):
			self.fVolumeI = 0;
			self.fVolumeF = 0;
			volumeFile = open(self.fVolumeFile , "r")
			volumeFile.readline()
			lines = volumeFile.readlines()
			#print("Start time: ", runStartTime)
			for i, line in enumerate(lines):
				currentLineSplit = line.split()
				currentDateTime = datetime.fromisoformat(currentLineSplit[0]+"+08:00")
				#print("Current time: ", currentDateTime, " - ", currentDateTime.timestamp())
				if(currentDateTime.timestamp() > runStartTime and self.fVolumeI == 0): 
					if(i>0):
						previousLineSplit = lines[i-1].split()
					else:
						previousLineSplit = currentLineSplit
					previousDateTime = datetime.fromisoformat(previousLineSplit[0]+"+08:00")
					currentVolume = float(currentLineSplit[3])
					previousVolume = float(previousLineSplit[3])
					# print("Found start")
					# print("  Previous time: ", previousDateTime.isoformat(), " - ", previousDateTime.timestamp())
					# print("  Run start time: ", datetime.fromtimestamp(runStartTime, tz=timezone.utc).isoformat(), " - ", runStartTime)
					# print("  Current time: ", currentDateTime.isoformat(), " - ", currentDateTime.timestamp())
					# print("  Previous vol: ", previousVolume, " - ", currentVolume)
					if(currentDateTime.timestamp() != previousDateTime.timestamp()):
						self.fVolumeI = previousVolume + (currentVolume-previousVolume)/(currentDateTime.timestamp()-previousDateTime.timestamp())*(runStartTime-previousDateTime.timestamp())
					else: self.fVolumeI = previousVolume

				if(currentDateTime.timestamp() > runStopTime and self.fVolumeF == 0): 
					if(i>0):
						previousLineSplit = lines[i-1].split()
					else:
						previousLineSplit = currentLineSplit
					previousDateTime = datetime.fromisoformat(previousLineSplit[0]+"+08:00")
					currentVolume = float(currentLineSplit[3])
					previousVolume = float(previousLineSplit[3])
					# print("Found stop")
					# print("  Previous time: ", previousDateTime.isoformat(), " - ", previousDateTime.timestamp())
					# print("  Run stop time: ", datetime.fromtimestamp(runStopTime, tz=timezone.utc).isoformat(), " - ", runStopTime)
					# print("  Current time: ", currentDateTime.isoformat(), " - ", currentDateTime.timestamp())
					# print("  Previous vol: ", previousVolume, " - ", currentVolume)
					if(currentDateTime.timestamp() != previousDateTime.timestamp()):
						self.fVolumeF = previousVolume + (currentVolume-previousVolume)/(currentDateTime.timestamp()-previousDateTime.timestamp())*(runStopTime-previousDateTime.timestamp())
					else: self.fVolumeF = previousVolume
					break

		print("Volume iniziale: %.1f"%self.fVolumeI)
		print("volume finale: %0.1f"%self.fVolumeF)

		#Compute volume list
		volume = []

		if (self.fStepTime != float("inf")) :
			t=self.fStepTime/2
			while(t+self.fStepTime/2 < self.fRunTime):
				volume.append(self.GetVolume(t))
				t+=self.fStepTime
			t-=self.fStepTime/2
			if(t < self.fRunTime):
				volume.append(self.GetVolume((t+self.fRunTime)/2))
		else : volume.append(self.fVolumeI)

		#Loop for TimeStep
		idxBiPo = 0
		idxStep = 0
		biPoBuffer = []

		timefromstart = 0

		while(True):
			if(idxBiPo>=len(BiPoList)): break
			idxStep+=1
			print("Start step ", idxStep)
			histoDT.Reset()
			histoEBi.Reset()
			histoEPo.Reset()
			biPoBuffer = []

			stepTime = BiPoList[idxBiPo].fTime
			while(idxBiPo<len(BiPoList)):
				if(BiPoList[idxBiPo].fTime > self.fStepTime * idxStep):
					break
				histoDT.Fill(BiPoList[idxBiPo].fDT)
				histoEBi.Fill(BiPoList[idxBiPo].fEBi)
				histoEPo.Fill(BiPoList[idxBiPo].fEPo)
				biPoBuffer.append(BiPoList[idxBiPo])
				idxBiPo+=1
			stepTime -= BiPoList[idxBiPo-1].fTime

			#print("TEST",len(BiPoList),idxBiPo)

			stepTime *= -1

			beginTime = runStartTime + timefromstart
			timefromstart += stepTime
			dt = datetime.fromtimestamp(beginTime,tz=timezone.utc)

			# Extract date and time
			begin_date_str = dt.strftime("%Y-%m-%d")
			begin_time_str = dt.strftime("%H:%M:%S")

			#DT Fit
			ffit = ROOT.TF1("FF", "[0]*0.693147/164.46e-6*exp(-x*0.693147/164.46e-6)+[1]", 0, self.fDelayMax)
			ffit.SetParameter(0, histoDT.GetEntries())
			ffit.SetParameter(1, histoDT.GetEntries() / 100)
			histoDT.Fit(ffit, "E")

			#Fit Results
			signalEvts = ffit.GetParameter(0) / (self.fDelayMax/100)
			bkgEvts = ffit.GetParameter(1) * self.fDelayMax / (self.fDelayMax/100)
			signalErr = ffit.GetParError(0) / (self.fDelayMax/100)
			bkgErr = ffit.GetParError(1) * self.fDelayMax / (self.fDelayMax/100)
			chi2 = ffit.GetChisquare()
			ndof = ffit.GetNDF()
			biPoActivity = 1000*signalEvts/(self.fEfficiency*volume[idxStep-1]*stepTime*(1-runDTPerc/100))
			biPoErrActivity = 1000*signalErr/(self.fEfficiency*volume[idxStep-1]*stepTime*(1-runDTPerc/100))
			print("Signal = %.1f ± %.1f"%(signalEvts, signalErr))
			print("Bkg = %.1f ± %.1f"%(bkgEvts, bkgErr))
			print("chi2 / ndof = %.1f/%d = %.1f"%(chi2 , ndof , chi2 / ndof ))
			print("StepTime (s) = %.1f"%(stepTime))
			print("Activity (mBq/m3) = %.2e ± %.2e"%(biPoActivity, biPoErrActivity))

			resultsFile.write("%s\t%s\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.2e\t%.2e\n"%(begin_date_str,begin_time_str,stepTime, signalEvts, signalErr, bkgEvts, bkgErr, chi2 / ndof, biPoActivity, biPoErrActivity))

			if(self.fSavePlot): 
				histoDT.Draw()

				latex=ROOT.TLatex()
				latex.SetNDC()
				latex.SetTextSize (0.03)
				latex.DrawText(0.5, 0.80, "Signal = %.1f$\\pm$%.1f"%(signalEvts, signalErr))
				latex.DrawText(0.5, 0.75, "Bkg = %.1f$\\pm$%.1f"%(bkgEvts, bkgErr))
				latex.DrawText(0.5, 0.7, "chi2 / ndof = %.1f/%d = %.1f"%(chi2 , ndof , chi2 / ndof ))

				if(self.fOutDir) : canvas.Print(self.fOutDir+"/"+runName+"_DT_"+str(idxStep)+".png")
				else : canvas.Print(runName+"/"+runName+"_DT_"+str(idxStep)+".png")
				histoAux.SetMaximum(histoEPo.GetBinContent(histoEPo.GetMaximumBin())*1.1)
				histoAux.SetMinimum(0.5)
				histoAux.Draw()
				histoEPo.Draw("same")
				histoEBi.Draw("same")
				if(self.fOutDir) : canvas.Print(self.fOutDir+"/"+runName+"_Energy_"+str(idxStep)+".png")
				else : canvas.Print(runName+"/"+runName+"_Energy_"+str(idxStep)+".png")
				print("Images saved")

			#Save root file with histograms
			if(self.fSaveRoot):
				if (self.fOutDir) : outFile = ROOT.TFile(self.fOutDir+"/"+runName+"_BiPo_"+str(idxStep)+".root", "RECREATE")
				else : outFile = ROOT.TFile(runName+"/"+runName+"_BiPo_"+str(idxStep)+".root", "RECREATE")
				outTree = ROOT.TTree("BiPo", "BiPo")
				dt=ROOT.std.vector("float")(0)
				eBi=ROOT.std.vector("float")(0)
				ePo=ROOT.std.vector("float")(0)
				outTree.Branch("DT", dt)
				outTree.Branch("EBi", eBi)
				outTree.Branch("EPo", ePo)
				
				for bipo in biPoBuffer:
					dt.clear()
					eBi.clear()
					ePo.clear()
					dt.push_back(bipo.fDT)
					eBi.push_back(bipo.fEBi)
					ePo.push_back(bipo.fEPo)
					outTree.Fill()
				
				histoDT.Write()
				histoEBi.Write()
				histoEPo.Write()

				outFile.Write()
				outFile.Close()
				print("Root file saved")

		resultsFile.close()

def main():

	parser = argparse.ArgumentParser(description="Process run file for BiPo analysis")
	parser.add_argument("-input", nargs='+', help="Run file to process", required=True)
	parser.add_argument("-stepTime", type=float, default=float("inf"), help="Compute the BiPo events every stepTime (hours - inf)")
	parser.add_argument("-eBiMin", type=float, default=3000, help="Minimum energy of Bi events (nPE - )")
	parser.add_argument("-eBiMax", type=float, default=9000, help="Maximum energy of Bi events (nPE - )")
	parser.add_argument("-ePoMin", type=float, default=2300, help="Minimum energy of Po events (nPE - )")
	parser.add_argument("-ePoMax", type=float, default=3000, help="Maximum energy of Po events (nPE - )")
	parser.add_argument("-delayMax", type=float, default=2e-3, help="Maximum delay for BiPo delayed coincidence (s - 2e-3)")
	parser.add_argument("-muTimeVeto", type=float, default=20e-6, help="Duration of muon veto (s - 20e-6)")
	parser.add_argument("-muEVeto", type=float, default=30000, help="Energy threshold for muon veto (nPE - 30000)")
	parser.add_argument("-efficiency", type=float, default=0.823 ,help="BiPo efficiency (- 0.823)")
	parser.add_argument("-volume", type=float, nargs='+', default=[1] ,help="LS volume. One value for fixed volume or two valus for initial and final volumes in the run (m3 - 1)")
	parser.add_argument("-volumeFile", default="", help="File with the filling volume info from http://junodqm1.ihep.ac.cn:5000/JUNO/LS_filling/download_file/massVolumeLS.txt")
	parser.add_argument("-gain", type=float, default=1 ,help="Gain applied to energy cuts")
	parser.add_argument("-offset", type=float, default=1 ,help="Offset adeed to energy cuts (after gain)")
	parser.add_argument("-savePlot", action="store_true", help="Save histograms of each step")
	parser.add_argument("-saveRoot", action="store_true", help="Save root file of each step")
	parser.add_argument("-outDir", default=None, help="Set a directory to store the output (complete path)")

	args = parser.parse_args()
	analysisManager = AnalysisManager()

	analysisManager.fRunName = args.input
	analysisManager.fStepTime = args.stepTime * 3600.
	analysisManager.fEBiMin = args.eBiMin * args.gain + args.offset
	analysisManager.fEBiMax = args.eBiMax * args.gain + args.offset
	analysisManager.fEPoMin = args.ePoMin * args.gain + args.offset
	analysisManager.fEPoMax = args.ePoMax * args.gain + args.offset
	analysisManager.fDelayMax = args.delayMax
	analysisManager.fMuEVeto = args.muEVeto
	analysisManager.fMuTimeVeto = args.muTimeVeto
	analysisManager.fEfficiency = args.efficiency
	analysisManager.fVolumeI = args.volume[0]
	if(len(args.volume)==2): 
		analysisManager.fVolumeF = args.volume[1]
	else:
		analysisManager.fVolumeF = analysisManager.fVolumeI
	analysisManager.fVolumeFile = args.volumeFile
	analysisManager.fSavePlot = args.savePlot
	analysisManager.fSaveRoot = args.saveRoot
	analysisManager.fOutDir = args.outDir

	for filePath in args.input:
		analysisManager.fRunPath = filePath
		analysisManager.ProcessIt()


if __name__ == "__main__":
	main()