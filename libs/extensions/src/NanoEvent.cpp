#include "NanoEvent.hpp"

#include "ExtensionsHelpers.hpp"

using namespace std;

TLorentzVector NanoEvent::GetMetFourVector() {
  TLorentzVector metVector;
  metVector.SetPtEtaPhiM(Get("MET_pt"), 0, Get("MET_phi"), 0);
  return metVector;
}

float NanoEvent::GetMetPt() { return Get("MET_pt"); }

shared_ptr<PhysicsObjects> NanoEvent::GetDRMatchedMuons(float matchingDeltaR,
                                                        shared_ptr<Collection<shared_ptr<PhysicsObject>>> muonCollection) {
  auto looseMuons = GetCollection("LooseMuons");
  auto looseDSAMuons = GetCollection("LooseDSAMuons");
  if (muonCollection != nullptr) {
    looseMuons = GetPATMuonsFromCollection(muonCollection);
    looseDSAMuons = GetDSAMuonsFromCollection(muonCollection);
  }

  auto allMuons = make_shared<PhysicsObjects>();
  for (auto muon : *looseMuons) {
    allMuons->push_back(muon);
  }
  for (auto dsaMuon : *looseDSAMuons) {
    auto dsaMuonP4 = asNanoMuon(dsaMuon)->GetFourVector();
    bool matchFound = false;
    for (auto muon : *looseMuons) {
      auto muonP4 = asNanoMuon(muon)->GetFourVector();
      if (muonP4.DeltaR(dsaMuonP4) < matchingDeltaR) matchFound = true;
    }
    if (matchFound == false) allMuons->push_back(dsaMuon);
  }

  return allMuons;
}

shared_ptr<PhysicsObjects> NanoEvent::GetOuterDRMatchedMuons(float matchingDeltaR,
                                                             shared_ptr<Collection<shared_ptr<PhysicsObject>>> muonCollection) {
  auto looseMuons = GetCollection("LooseMuons");
  auto looseDSAMuons = GetCollection("LooseDSAMuons");
  if (muonCollection != nullptr) {
    looseMuons = GetPATMuonsFromCollection(muonCollection);
    looseDSAMuons = GetDSAMuonsFromCollection(muonCollection);
  }

  auto allMuons = make_shared<PhysicsObjects>();
  for (auto muon : *looseMuons) {
    allMuons->push_back(muon);
  }
  for (auto dsaMuon : *looseDSAMuons) {
    bool matchFound = false;
    for (auto muon : *looseMuons) {
      if (asNanoMuon(dsaMuon)->OuterDeltaRtoMuon(asNanoMuon(muon)) < matchingDeltaR) matchFound = true;
    }
    if (matchFound == false) allMuons->push_back(dsaMuon);
  }

  return allMuons;
}

shared_ptr<PhysicsObjects> NanoEvent::GetProximityDRMatchedMuons(float matchingDeltaR,
                                                                 shared_ptr<Collection<shared_ptr<PhysicsObject>>> muonCollection) {
  auto looseMuons = GetCollection("LooseMuons");
  auto looseDSAMuons = GetCollection("LooseDSAMuons");
  if (muonCollection != nullptr) {
    looseMuons = GetPATMuonsFromCollection(muonCollection);
    looseDSAMuons = GetDSAMuonsFromCollection(muonCollection);
  }

  auto allMuons = make_shared<PhysicsObjects>();
  for (auto muon : *looseMuons) {
    allMuons->push_back(muon);
  }
  for (auto dsaMuon : *looseDSAMuons) {
    bool matchFound = false;
    for (auto muon : *looseMuons) {
      auto vertex = GetVertexForDimuon(dsaMuon, muon);
      if (float(vertex->at(0)->Get("dRprox")) < matchingDeltaR) matchFound = true;
    }
    if (matchFound == false) allMuons->push_back(dsaMuon);
  }

  return allMuons;
}

shared_ptr<PhysicsObjects> NanoEvent::GetSegmentMatchedMuons(float minMatchRatio,
                                                             shared_ptr<Collection<shared_ptr<PhysicsObject>>> muonCollection) {
  auto looseMuons = GetCollection("LooseMuons");
  auto looseDSAMuons = GetCollection("LooseDSAMuons");
  if (muonCollection != nullptr) {
    looseMuons = GetPATMuonsFromCollection(muonCollection);
    looseDSAMuons = GetDSAMuonsFromCollection(muonCollection);
  }

  auto allMuons = make_shared<PhysicsObjects>();
  for (auto muon : *looseMuons) {
    allMuons->push_back(muon);
  }
  for (auto dsaMuon : *looseDSAMuons) {
    float nSegments = float(dsaMuon->Get("nSegments"));

    bool matchFound = false;
    for (int i = 1; i <= 5; i++) {
      float ratio_tmp = asNanoMuon(dsaMuon)->GetMatchesForNthBestMatch(i) / nSegments;
      if (!matchFound && ratio_tmp >= minMatchRatio) {
        matchFound = PATMuonIndexExist(looseMuons, asNanoMuon(dsaMuon)->GetMatchIdxForNthBestMatch(i));
        break;
      }
    }
    if (matchFound == false) allMuons->push_back(dsaMuon);
  }

  return allMuons;
}

bool NanoEvent::DSAMuonIndexExist(shared_ptr<PhysicsObjects> objectCollection, float index) {
  return MuonIndexExist(objectCollection, index, true);
}

bool NanoEvent::PATMuonIndexExist(shared_ptr<PhysicsObjects> objectCollection, float index) {
  return MuonIndexExist(objectCollection, index, false);
}

bool NanoEvent::MuonIndexExist(shared_ptr<PhysicsObjects> objectCollection, float index, bool isDSAMuon) {
  for (auto object : *objectCollection) {
    if (float(object->Get("idx")) == index) {
      if (isDSAMuon && asNanoMuon(object)->isDSAMuon()) return true;
      if (!isDSAMuon && !asNanoMuon(object)->isDSAMuon()) return true;
    }
  }
  return false;
}

float NanoEvent::DeltaR(float eta1, float phi1, float eta2, float phi2) {
  float dEta = eta1 - eta2;
  float dPhi = TVector2::Phi_mpi_pi(phi1 - phi2);
  return TMath::Sqrt(dEta * dEta + dPhi * dPhi);
}

shared_ptr<PhysicsObjects> NanoEvent::GetAllMuonVerticesCollection() {
  auto patVertices = GetCollection("PatMuonVertex");
  auto patDsaVertices = GetCollection("PatDSAMuonVertex");
  auto dsaVertices = GetCollection("DSAMuonVertex");

  auto muonVertices = make_shared<PhysicsObjects>();

  for (auto vertex : *patVertices) {
    muonVertices->push_back(vertex);
  }
  for (auto vertex : *patDsaVertices) {
    muonVertices->push_back(vertex);
  }
  for (auto vertex : *dsaVertices) {
    muonVertices->push_back(vertex);
  }
  return muonVertices;
}

shared_ptr<PhysicsObjects> NanoEvent::GetVerticesForMuons(shared_ptr<PhysicsObjects> muonCollection) {
  auto vertices = GetAllMuonVerticesCollection();
  auto muonVertices = make_shared<PhysicsObjects>();

  for (auto vertex : *vertices) {
    bool foundMuon1 = false;
    bool foundMuon2 = false;
    for (auto muon : *muonCollection) {
      bool isDSAMuon = asNanoMuon(muon)->isDSAMuon();
      bool isDSAMuon1 = float(vertex->Get("isDSAMuon1")) == 1;
      bool isDSAMuon2 = float(vertex->Get("isDSAMuon2")) == 1;
      float muonIndex = muon->Get("idx");
      float muonIndex1 = vertex->Get("originalMuonIdx1");
      float muonIndex2 = vertex->Get("originalMuonIdx2");

      foundMuon1 |= (isDSAMuon1 == isDSAMuon) && (muonIndex == muonIndex1);
      foundMuon2 |= (isDSAMuon2 == isDSAMuon) && (muonIndex == muonIndex2);
    }
    if (foundMuon1 && foundMuon2) muonVertices->push_back(vertex);
  }

  return muonVertices;
}

shared_ptr<PhysicsObjects> NanoEvent::GetVertexForDimuon(shared_ptr<PhysicsObject> muon1, shared_ptr<PhysicsObject> muon2) {
  auto muons = make_shared<PhysicsObjects>();
  muons->push_back(muon1);
  muons->push_back(muon2);
  auto dimuonVertex = GetVerticesForMuons(muons);

  return dimuonVertex;
}

float NanoEvent::GetNDSAMuon(string collectionName) {
  auto collection = GetCollection(collectionName);

  float nDSAMuon = 0;
  for (auto object : *collection) {
    if (asNanoMuon(object)->isDSAMuon()) nDSAMuon++;
  }
  return nDSAMuon;
}

float NanoEvent::GetNMuon(string collectionName) {
  auto collection = GetCollection(collectionName);

  float nMuon = 0;
  for (auto object : *collection) {
    if (!asNanoMuon(object)->isDSAMuon()) nMuon++;
  }
  return nMuon;
}

shared_ptr<PhysicsObject> NanoEvent::GetDSAMuonWithIndex(int muon_idx, string collectionName) {
  return GetPATorDSAMuonWithIndex(muon_idx, collectionName, true);
}

shared_ptr<PhysicsObject> NanoEvent::GetPATMuonWithIndex(int muon_idx, string collectionName) {
  return GetPATorDSAMuonWithIndex(muon_idx, collectionName, false);
}

shared_ptr<PhysicsObject> NanoEvent::GetPATorDSAMuonWithIndex(int muon_idx, string collectionName, bool doDSAMuons) {
  auto collection = GetCollection(collectionName);

  for (auto object : *collection) {
    float idx = object->Get("idx");
    bool isDSAmuon = asNanoMuon(object)->isDSAMuon();
    if (idx != muon_idx) continue;
    if (isDSAmuon && doDSAMuons) return object;
    if (!isDSAmuon && !doDSAMuons) return object;
  }
  return nullptr;
}

pair<float, int> NanoEvent::GetDeltaRandIndexOfClosestGenMuon(shared_ptr<PhysicsObject> recoMuon) {
  auto genParticles = event->GetCollection("GenPart");
  float minDR = 999.;
  int minDRIdx = -1;

  auto recoMuonFourVector = asNanoMuon(recoMuon)->GetFourVector();
  float muonMass = 0.105;

  for (int idx = 0; idx < genParticles->size(); idx++) {
    auto genMuon = genParticles->at(idx);
    auto genMuonFourVector = asNanoGenParticle(genMuon)->GetFourVector(muonMass);
    float dR = genMuonFourVector.DeltaR(recoMuonFourVector);
    if (dR < minDR) {
      minDR = dR;
      minDRIdx = idx;
    }
  }
  return make_pair(minDR, minDRIdx);
}

shared_ptr<PhysicsObjects> NanoEvent::GetDSAMuonsFromCollection(string muonCollectionName) {
  auto muonCollection = GetCollection(muonCollectionName);
  return GetDSAMuonsFromCollection(muonCollection);
}

shared_ptr<PhysicsObjects> NanoEvent::GetDSAMuonsFromCollection(shared_ptr<Collection<shared_ptr<PhysicsObject>>> muonCollection) {
  auto dsaMuons = make_shared<PhysicsObjects>();
  for (auto muon : *muonCollection) {
    if (asNanoMuon(muon)->isDSAMuon()) dsaMuons->push_back(muon);
  }
  return dsaMuons;
}

shared_ptr<PhysicsObjects> NanoEvent::GetPATMuonsFromCollection(string muonCollectionName) {
  auto muonCollection = GetCollection(muonCollectionName);
  return GetPATMuonsFromCollection(muonCollection);
}

shared_ptr<PhysicsObjects> NanoEvent::GetPATMuonsFromCollection(shared_ptr<Collection<shared_ptr<PhysicsObject>>> muonCollection) {
  auto patMuons = make_shared<PhysicsObjects>();
  for (auto muon : *muonCollection) {
    if (!asNanoMuon(muon)->isDSAMuon()) patMuons->push_back(muon);
  }
  return patMuons;
}

shared_ptr<Collection<shared_ptr<PhysicsObject>>> NanoEvent::GetAllCommonMuonsInCollections(
    shared_ptr<Collection<shared_ptr<PhysicsObject>>> muonCollection1, shared_ptr<Collection<shared_ptr<PhysicsObject>>> muonCollection2) {
  shared_ptr<Collection<shared_ptr<PhysicsObject>>> muonCollection;
  for (auto muon : *muonCollection1) {
    if (MuonIndexExist(muonCollection2, muon->Get("idx"), asNanoMuon(muon)->isDSAMuon())) {
      muonCollection->push_back(muon);
    }
  }
  return muonCollection;
}