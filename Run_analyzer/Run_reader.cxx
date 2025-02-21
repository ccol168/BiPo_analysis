#define SNIPER_VERSION_2 1
#include "Run_reader.h"
#include "Identifier/IDService.h"
#include "BufferMemMgr/IDataMemMgr.h"
#include "EvtNavigator/NavBuffer.h"
#include "EvtNavigator/EvtNavHelper.h"
#include "SniperKernel/AlgFactory.h"
#include "SniperKernel/SniperLog.h"
#include "Event/SimHeader.h"
#include "Event/CdLpmtCalibHeader.h"
#include "Event/CdLpmtCalibEvt.h"
#include "Event/CdTriggerHeader.h"
#include "Event/CdTriggerEvt.h"
#include "Event/WpCalibHeader.h"
#include "Event/WpCalibEvt.h"
#include "Event/WpTriggerHeader.h"
#include "Event/WpTriggerEvt.h"
#include "Event/CdVertexRecHeader.h"
#include "Event/CdVertexRecEvt.h"
#include "RootWriter/RootWriter.h"
#include <numeric>

#include "TH1F.h"
#include "TTree.h"

DECLARE_ALGORITHM(Run_reader);

Run_reader::Run_reader(const std::string& name) 
	: AlgBase(name),
	  m_iEvt(0),
	  m_buf(0)
{
}

bool Run_reader::initialize() {

    LogDebug << "initializing" << std::endl;
    auto toptask = getRoot();

    idServ = IDService::getIdServ();
    idServ->init();
	
    SniperDataPtr<JM::NavBuffer> navBuf(getParent(), "/Event");

    if ( navBuf.invalid() ) {
        LogError << "cannot get the NavBuffer @ /Event" << std::endl;
        return false;
    }
	
    m_buf = navBuf.data();

    SniperPtr<RootWriter> rw(getParent(), "RootWriter");
    if (rw.invalid()) {
        LogError << "Can't Locate RootWriter. If you want to use it, please "
                 << "enable it in your job option file."
                 << std::endl;
         return false;
    }

    //wp_events_seen = 0;    
    events = rw->bookTree(*m_par,"tree/CdEvents","Events Tree");
    //events->Branch("EvtID",&cdEvtID,"EvtID/I");
    events->Branch("TimeStamp",&timestamp);
    //events->Branch("PMTID",&PMTID);
    //events->Branch("Charge",&charge);
    //events->Branch("Time",&time);
    events->Branch("NPE",&total_npe,"npe/F");
    events->Branch("TriggerType",&trigger_type);
    //events->Branch("Recox",&CdRecox);
    //events->Branch("Recoy",&CdRecoy);
    //events->Branch("Recoz",&CdRecoz);
    //events->Branch("Recopx",&CdRecopx);
    //events->Branch("Recopy",&CdRecopy);
    //events->Branch("Recopz",&CdRecopz);
    //events->Branch("RecoEnergy",&CdRecoenergy);
    //events->Branch("RecoPE",&CdRecoPESum);
    //events->Branch("Recot0",&CdRecot0);
    //events->Branch("RecoEnergyQuality",&CdRecoEnergyQuality);
    //events->Branch("RecoPositionQuality",&CdRecoPositionQuality);
/*
    events->Branch("x_CM",&x_CM,"x_CM/F");
    events->Branch("y_CM",&y_CM,"y_CM/F");
    events->Branch("z_CM",&z_CM,"z_CM/F");

    wpEvents = rw->bookTree(*m_par,"tree/WpEvents","Water pool Events Tree");
    wpEvents->Branch("EvtID",&wpEvtID,"EvtID/I");
    wpEvents->Branch("TimeStamp",&wptimestamp);
    wpEvents->Branch("PMTID",&wpPMTID);
    wpEvents->Branch("Charge",&wpcharge);
    wpEvents->Branch("Time",&wptime);
    wpEvents->Branch("NPE",&wptotal_npe,"npe/F");
    wpEvents->Branch("TriggerType",&wptrigger_type);
*/
    return true;
}

bool Run_reader::execute() {

    LogDebug << "=====================================" << std::endl;
    LogDebug << "executing: " << m_iEvt++
             << std::endl;

    JM::CdLpmtCalibEvt* calibevent = 0;
    JM::CdTriggerEvt* triggerevent = 0;


    auto nav = m_buf->curEvt();
//    const auto& paths = nav->getPath();

    auto calibheader = JM::getHeaderObject<JM::CdLpmtCalibHeader>(nav);
    if (calibheader) calibevent = (JM::CdLpmtCalibEvt*)calibheader->event();

    if (!calibevent) {
        LogInfo << "No CalibEvt or WpEvt found, skipping..." << std::endl;
        return true;
    }
    if (calibevent) {

        auto triggerheader = JM::getHeaderObject<JM::CdTriggerHeader>(nav);
        if (triggerheader) triggerevent = (JM::CdTriggerEvt*) triggerheader -> event();

        if (!triggerevent) {
            LogInfo << "No CdTriggerEvt found for this event " << std::endl;
            trigger_type = "None";
        } else {
            const auto& triggerelement = triggerevent -> triggerType();
            if (triggerelement.size() != 1) LogInfo << "------------- Strange trigger element! -------------" << std::endl;
            else trigger_type = triggerelement[0];
        }

	
        charge.clear();
        time.clear();
        PMTID.clear();
	
        for (const auto& element : calibevent->calibPMTCol()) {

            //PMTID.push_back(element->pmtId());

            for (auto pmtChannel : element -> charge() ) {
                charge.push_back(pmtChannel);
		//int PmtNo = idServ->id2CopyNo(Identifier(element->pmtId()));
               // PMTID.push_back(PmtNo);

            }
           // for (auto pmtChannel : element -> time() ) {
           //     time.push_back(pmtChannel);
           // }

        }

        total_npe = std::accumulate(charge.begin(),charge.end(),0.0);

        timestamp = nav->TimeStamp();
        events -> Fill();

    	}
    return true;

}

bool Run_reader::finalize() {

    return true;
    
}
