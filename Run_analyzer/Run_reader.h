#ifndef RUN_READER_H
#define RUN_READER_H

#include "SniperKernel/AlgBase.h"
#include "EvtNavigator/NavBuffer.h"
#include "Identifier/IDService.h"
#include <fstream>
#include <map>

class TH1F;
class TTree;

class Run_reader : public AlgBase //Change the name to something more descriptive
{
    public :
        Run_reader() : Run_reader("Run_reader") {}
        Run_reader(const std::string& name); //Constructor, must have same name as the class

    // Following functions are needed by SNiPER, so they are mandatory
        bool initialize();
        bool execute();
        bool finalize();

    private :

        int m_iEvt; // To count the loops
        JM::NavBuffer* m_buf; // Our buffer with the events
        
        // Define variables that are globally used
        IDService* idServ;
	TTimeStamp timestamp;
        float total_npe, my_total_npe;
        std::vector<int> PMTID; 
        std::vector<float> charge ,time;
	//float x_CM, y_CM, z_CM;
        TString trigger_type; //, wptrigger_type;
	//float CdRecox, CdRecoy, CdRecoz, CdRecopx, CdRecopy, CdRecopz, CdRecoenergy,CdRecoPESum,CdRecot0, CdRecoPositionQuality, CdRecoEnergyQuality;
	//int wp_events_seen;

        TTree* events ;
	//TTree* wpEvents;
	//map <int,tuple<int,double,double,double,double,double>> Map_PMTs;


};

#endif

