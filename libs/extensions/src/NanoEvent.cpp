#include "NanoEvent.hpp"

#include "ExtensionsHelpers.hpp"

using namespace std;

TLorentzVector NanoEvent::GetMetFourVector() {
  TLorentzVector metVector;
  metVector.SetPtEtaPhiM(Get("MET_pt"), 0, Get("MET_phi"), 0);
  return metVector;
}

float NanoEvent::GetMetPt() { return Get("MET_pt"); }

shared_ptr<NanoMuons> NanoEvent::GetDRMatchedMuons(shared_ptr<NanoMuons> muonCollection, float matchingDeltaR) {
  auto loosePATMuons = GetPATMuonsFromCollection(muonCollection);
  auto looseDSAMuons = GetDSAMuonsFromCollection(muonCollection);

  auto allMuons = make_shared<NanoMuons>();
  for (auto muon : *loosePATMuons) {
    allMuons->push_back(muon);
  }
  for (auto dsaMuon : *looseDSAMuons) {
    auto dsaMuonP4 = dsaMuon->GetFourVector();
    bool matchFound = false;
    for (auto muon : *loosePATMuons) {
      auto muonP4 = muon->GetFourVector();
      if (muonP4.DeltaR(dsaMuonP4) < matchingDeltaR) {
        matchFound = true;
        break;
      }
    }
    if (matchFound == false) allMuons->push_back(dsaMuon);
  }

  return allMuons;
}

shared_ptr<NanoMuons> NanoEvent::GetOuterDRMatchedMuons(shared_ptr<NanoMuons> muonCollection, float matchingDeltaR) {
  auto loosePATMuons = GetPATMuonsFromCollection(muonCollection);
  auto looseDSAMuons = GetDSAMuonsFromCollection(muonCollection);

  auto allMuons = make_shared<NanoMuons>();
  for (auto muon : *loosePATMuons) {
    allMuons->push_back(muon);
  }
  for (auto dsaMuon : *looseDSAMuons) {
    bool matchFound = false;
    for (auto muon : *loosePATMuons) {
      if (dsaMuon->OuterDeltaRtoMuon(muon) < matchingDeltaR) {
        matchFound = true;
        break;
      }
    }
    if (matchFound == false) allMuons->push_back(dsaMuon);
  }

  return allMuons;
}

shared_ptr<NanoMuons> NanoEvent::GetProximityDRMatchedMuons(shared_ptr<NanoMuons> muonCollection, float matchingDeltaR) {
  auto loosePATMuons = GetPATMuonsFromCollection(muonCollection);
  auto looseDSAMuons = GetDSAMuonsFromCollection(muonCollection);

  auto allMuons = make_shared<NanoMuons>();
  for (auto muon : *loosePATMuons) {
    allMuons->push_back(muon);
  }
  for (auto dsaMuon : *looseDSAMuons) {
    bool matchFound = false;
    for (auto muon : *loosePATMuons) {
      auto vertex = GetVertexForDimuon(dsaMuon, muon);
      if (float(vertex->Get("dRprox")) < matchingDeltaR) {
        matchFound = true;
        break;
      }
    }
    if (matchFound == false) allMuons->push_back(dsaMuon);
  }

  return allMuons;
}

shared_ptr<NanoMuons> NanoEvent::GetSegmentMatchedMuons(shared_ptr<NanoMuons> muonCollection, float minMatchRatio) {
  auto loosePATMuons = GetPATMuonsFromCollection(muonCollection);
  auto looseDSAMuons = GetDSAMuonsFromCollection(muonCollection);

  auto allMuons = make_shared<NanoMuons>();
  for (auto muon : *loosePATMuons) {
    allMuons->push_back(muon);
  }
  for (auto dsaMuon : *looseDSAMuons) {
    float nSegments = float(dsaMuon->Get("nSegments"));

    bool matchFound = false;
    for (int i = 1; i <= 5; i++) {
      float ratio_tmp = dsaMuon->GetMatchesForNthBestMatch(i) / nSegments;
      if (!matchFound && ratio_tmp >= minMatchRatio) {
        matchFound = PATMuonIndexExist(loosePATMuons, dsaMuon->GetMatchIdxForNthBestMatch(i));
        if(matchFound) break;
      }
    }
    if (matchFound == false) allMuons->push_back(dsaMuon);
  }

  return allMuons;
}

shared_ptr<PhysicsObject> NanoEvent::GetSegmentMatchedBestMuonVertex(shared_ptr<PhysicsObject> bestVertex, shared_ptr<PhysicsObjects> goodVerticesCollection, float minMatchRatio) {
  auto nanoVertex = asNanoDimuonVertex(bestVertex,event);
  // Pat-PAT dimuon vertex
  if (nanoVertex->IsPatDimuon()) return bestVertex;

  auto patVertexCollection = make_shared<PhysicsObjects>();
  auto patDSAVertexCollection = make_shared<PhysicsObjects>();
  for (auto goodVertex : *goodVerticesCollection) {
    if (asNanoDimuonVertex(goodVertex,event)->IsPatDimuon()) {
      patVertexCollection->push_back(goodVertex);
    }
    if (asNanoDimuonVertex(goodVertex,event)->IsPatDSADimuon()) {
      patDSAVertexCollection->push_back(goodVertex);
    }
  }
  // DSA-DSA dimuon vertex
  if (nanoVertex->IsDSADimuon()) {
    auto dsaMuon1 = nanoVertex->Muon1();
    auto dsaMuon2 = nanoVertex->Muon2();
    float nSegments1 = dsaMuon1->Get("nSegments");
    float nSegments2 = dsaMuon2->Get("nSegments");
    vector<int> patMatchIndices1;
    vector<int> patMatchIndices2;
    // Get all mathed PAT muons
    for (int i = 1; i <= 5; i++) {
      float ratio_tmp1 = dsaMuon1->GetMatchesForNthBestMatch(i) / nSegments1;
      float ratio_tmp2 = dsaMuon2->GetMatchesForNthBestMatch(i) / nSegments2;

      if(ratio_tmp1 >= minMatchRatio) {
        patMatchIndices1.push_back(dsaMuon1->GetMatchIdxForNthBestMatch(i));
      }
      if(ratio_tmp2 >= minMatchRatio) {
        patMatchIndices2.push_back(dsaMuon2->GetMatchIdxForNthBestMatch(i));
      }
    }
    int matchedVertexIdx = -1;
    float minChi2 = 9999.;
    // Check if any PAT muon combinations are in patVertexCollection
    // If more than one vertex we select the one with lowest chi2
    for (auto matchIndex1 : patMatchIndices1) {
      for (auto matchIndex2 : patMatchIndices2) {
        if (matchIndex1 == matchIndex2) continue;
        for (int i=0; i<patVertexCollection->size(); i++) {
          auto patVertex = patVertexCollection->at(i);
          auto muon1 = asNanoDimuonVertex(patVertex,event)->Muon1();
          auto muon2 = asNanoDimuonVertex(patVertex,event)->Muon2();
          if (((float)muon1->Get("idx") == matchIndex1 && (float)muon2->Get("idx") == matchIndex2) || 
            ((float)muon1->Get("idx") == matchIndex2 && (float)muon2->Get("idx") == matchIndex1)) {          
            if ((float)patVertex->Get("normChi2") < minChi2) {
              matchedVertexIdx = i;
              minChi2 = (float)patVertex->Get("normChi2");
            }
          }
        }
      }
    }
    if (matchedVertexIdx > -1) {
      auto newVertex = patVertexCollection->at(matchedVertexIdx);
      return newVertex;
    }
    // Check if any PAT-DSA muon combinations are in patDSAVertexCollection
    matchedVertexIdx = -1;
    minChi2 = 9999.;
    for (auto matchIndex1 : patMatchIndices1) {
      for (auto matchIndex2 : patMatchIndices2) {
        for (int i=0; i<patDSAVertexCollection->size(); i++) {
          auto patDSAVertex = patDSAVertexCollection->at(i);
          auto muon1 = asNanoDimuonVertex(patDSAVertex,event)->Muon1();
          if ((float)muon1->Get("idx") == matchIndex1 && (float)muon1->Get("idx") == matchIndex2) {          
            if ((float)patDSAVertex->Get("normChi2") < minChi2) {
              matchedVertexIdx = i;
              minChi2 = (float)patDSAVertex->Get("normChi2");
            }
          }
        }
      }
    }
    if (matchedVertexIdx > -1) {
      auto newVertex = patDSAVertexCollection->at(matchedVertexIdx);
      return newVertex;
    }
    return bestVertex;
  }
  // PAT-DSA dimuon vertex
  if (nanoVertex->IsPatDSADimuon()) {
    auto patMuon = nanoVertex->Muon1();
    auto dsaMuon = nanoVertex->Muon2();
    float nSegments = dsaMuon->Get("nSegments");
    float patMatchIndex1 = patMuon->Get("idx");
    vector<int> patMatchIndices2;
    // Get all mathed PAT muons
    for (int i = 1; i <= 5; i++) {
      float ratio_tmp = dsaMuon->GetMatchesForNthBestMatch(i) / nSegments;
      if(ratio_tmp >= minMatchRatio) {
        patMatchIndices2.push_back(dsaMuon->GetMatchIdxForNthBestMatch(i));
      }
    }
    // Check if any PAT muon combinations are in patVertexCollection
    int matchedVertexIdx = -1;
    float minChi2 = 9999.;
    for (auto matchIndex2 : patMatchIndices2) {
      if (patMatchIndex1 == matchIndex2) continue;
      for (int i=0; i<patVertexCollection->size(); i++) {
        auto patVertex = patVertexCollection->at(i);
        auto muon1 = asNanoDimuonVertex(patVertex,event)->Muon1();
        auto muon2 = asNanoDimuonVertex(patVertex,event)->Muon2();
        if ((float)muon1->Get("idx") == patMatchIndex1 && (float)muon2->Get("idx") == matchIndex2) {          
          if ((float)patVertex->Get("normChi2") < minChi2) {
            matchedVertexIdx = i;
            minChi2 = (float)patVertex->Get("normChi2");
          }
        }
      }
    }
    if (matchedVertexIdx > -1) {
      auto newVertex = patDSAVertexCollection->at(matchedVertexIdx);
      return newVertex;
    }
    return bestVertex;
  }
  return bestVertex;
}

bool NanoEvent::DSAMuonIndexExist(shared_ptr<NanoMuons> muons, float index) {
  return MuonIndexExist(muons, index, true);
}

bool NanoEvent::PATMuonIndexExist(shared_ptr<NanoMuons> muons, float index) {
  return MuonIndexExist(muons, index, false);
}

bool NanoEvent::MuonIndexExist(shared_ptr<NanoMuons> muons, float index, bool isDSAMuon) {
  for (auto muon : *muons) {
    if (float(muon->Get("idx")) == index) {
      if (isDSAMuon && muon->IsDSA()) return true;
      if (!isDSAMuon && !muon->IsDSA()) return true;
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

shared_ptr<PhysicsObjects> NanoEvent::GetVerticesForMuons(shared_ptr<NanoMuons> muonCollection) {
  auto vertices = GetAllMuonVerticesCollection();
  auto muonVertices = make_shared<PhysicsObjects>();

  for (auto vertex : *vertices) {
    bool foundMuon1 = false;
    bool foundMuon2 = false;
    for (auto muon : *muonCollection) {
      bool isDSAMuon = muon->IsDSA();
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

shared_ptr<PhysicsObject> NanoEvent::GetVertexForDimuon(shared_ptr<NanoMuon> muon1, shared_ptr<NanoMuon> muon2) {
  auto muons = make_shared<NanoMuons>();
  muons->push_back(muon1);
  muons->push_back(muon2);
  auto dimuonVertex = GetVerticesForMuons(muons);
  if(dimuonVertex->size()<1) return nullptr;
  return dimuonVertex->at(0);
}

std::shared_ptr<PhysicsObjects> NanoEvent::GetVerticesForDimuons(shared_ptr<NanoMuonPairs> dimuons) {
  auto muonVertices = make_shared<PhysicsObjects>();
  for (auto dimuon : *dimuons) {
    auto vertex = GetVertexForDimuon(dimuon.first, dimuon.second);
    if(vertex) muonVertices->push_back(vertex);
  }  
  return muonVertices;
}

float NanoEvent::GetNDSAMuon(string collectionName) {
  auto collection = GetCollection(collectionName);

  float nDSAMuon = 0;
  for (auto object : *collection) {
    if (asNanoMuon(object)->IsDSA()) nDSAMuon++;
  }
  return nDSAMuon;
}

float NanoEvent::GetNMuon(string collectionName) {
  auto collection = GetCollection(collectionName);

  float nMuon = 0;
  for (auto object : *collection) {
    if (!asNanoMuon(object)->IsDSA()) nMuon++;
  }
  return nMuon;
}

shared_ptr<NanoMuon> NanoEvent::GetDSAMuonWithIndex(int muon_idx, string collectionName) {
  return GetPATorDSAMuonWithIndex(muon_idx, collectionName, true);
}

shared_ptr<NanoMuon> NanoEvent::GetPATMuonWithIndex(int muon_idx, string collectionName) {
  return GetPATorDSAMuonWithIndex(muon_idx, collectionName, false);
}

shared_ptr<NanoMuon> NanoEvent::GetPATorDSAMuonWithIndex(int muon_idx, string collectionName, bool doDSAMuons) {
  auto collection = GetCollection(collectionName);

  for (auto object : *collection) {
    auto muon = asNanoMuon(object);

    float idx = muon->Get("idx");
    bool isDSAmuon = muon->IsDSA();
    if (idx != muon_idx) continue;
    if (isDSAmuon && doDSAMuons) return muon;
    if (!isDSAmuon && !doDSAMuons) return muon;
  }
  return nullptr;
}

pair<float, int> NanoEvent::GetDeltaRandIndexOfClosestGenMuon(shared_ptr<NanoMuon> recoMuon) {
  auto genParticles = event->GetCollection("GenPart");
  float minDR = 999.;
  int minDRIdx = -1;

  auto recoMuonFourVector = recoMuon->GetFourVector();
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

shared_ptr<NanoMuons> NanoEvent::GetDSAMuonsFromCollection(string muonCollectionName) {
  auto muonCollection = GetCollection(muonCollectionName);
  return GetDSAMuonsFromCollection(asNanoMuons(muonCollection));
}

shared_ptr<NanoMuons> NanoEvent::GetDSAMuonsFromCollection(shared_ptr<NanoMuons> muonCollection) {
  auto dsaMuons = make_shared<NanoMuons>();
  for (auto muon : *muonCollection) {
    if (muon->IsDSA()) dsaMuons->push_back(muon);
  }
  return dsaMuons;
}

shared_ptr<NanoMuons> NanoEvent::GetPATMuonsFromCollection(string muonCollectionName) {
  auto muonCollection = GetCollection(muonCollectionName);
  return GetPATMuonsFromCollection(asNanoMuons(muonCollection));
}

shared_ptr<NanoMuons> NanoEvent::GetPATMuonsFromCollection(shared_ptr<NanoMuons> muonCollection) {
  auto patMuons = make_shared<NanoMuons>();
  for (auto muon : *muonCollection) {
    if (!muon->IsDSA()) patMuons->push_back(muon);
  }
  return patMuons;
}

shared_ptr<NanoMuons> NanoEvent::GetAllCommonMuonsInCollections(shared_ptr<NanoMuons> muonCollection1, shared_ptr<NanoMuons> muonCollection2) {
  auto muonCollection = make_shared<NanoMuons>();
  for (auto muon : *muonCollection1) {
    if (MuonIndexExist(muonCollection2, muon->Get("idx"), muon->IsDSA())) {
      muonCollection->push_back(muon);
    }
  }
  return muonCollection;
}