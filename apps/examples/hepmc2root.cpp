#include <string>
#include <regex>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>

#include <TFile.h>
#include <TTree.h>

using namespace std;

const int n_particles = 5000;
int n_daughters = 100;

struct Event {
  int    Event_numberP;
  int    Event_processID;
  int    Event_number;
  int    Event_numberMP;
  float  Event_scale;
  float  Event_alphaQCD;
  float  Event_alphaQED;
  int    Event_barcodeSPV;
  int    Event_numberV;
  int    Event_barcodeBP1;
  int    Event_barcodeBP2;
  
  float Xsection_value;
  float Xsection_error;
  
  int   PDF_parton1;
  int   PDF_parton2;
  float PDF_x1;
  float PDF_x2;
  float PDF_Q2;
  float PDF_x1f;
  float PDF_x2f;
  int   PDF_id1;
  int   PDF_id2;
  
  float Particle_x[n_particles];
  float Particle_y[n_particles];
  float Particle_z[n_particles];
  float Particle_ctau[n_particles];
  int   Particle_barcode[n_particles];
  int   Particle_pid[n_particles];
  float Particle_px[n_particles];
  float Particle_py[n_particles];
  float Particle_pz[n_particles];
  float Particle_energy[n_particles];
  float Particle_mass[n_particles];
  int   Particle_status[n_particles];
  int   Particle_d[100][n_particles];
};

string makeBranchName(string input, string type="F")
{
  return (input+"[Event_numberP]/"+type).c_str();
}

class hepmc2root
{
public:
  hepmc2root(string input_file_name, string output_file_name = ""){
    input_file = ifstream(input_file_name);
    file = new TFile(output_file_name.c_str(), "recreate");
    tree = new TTree("Events", "HEPMC_tree");
    
    event = Event();
    setup_branches();
  }
  ~hepmc2root(){}
  
  bool process(){
    
    string line;
    bool found_event = false;
    
    while(getline(input_file, line)){
      get_tokens(line);
      if(tokens.size()==0) continue;
      if(tokens[0] != "E") continue;
      found_event = true;
      break;
    }
    if(!found_event) return false;
    
    set_event_variables();
    vertex.clear();
    
    bool for_line_broken = false;
    
    while(getline(input_file, line)){
      get_tokens(line);
      string key = tokens[0];
      
      if(key == 'C') set_xsec_variables();
      else if(key == 'F') set_pdf_variables();
      else if(key == 'V'){
        int vbarcode = stoi(tokens[1]);
        
        vertex[vbarcode] = vector<int>(n_daughters, -1);
        
        float x    = stod(tokens[3]);
        float y    = stod(tokens[4]);
        float z    = stod(tokens[5]);
        float ctau = stod(tokens[6]);
        int nout   = stoi(tokens[8]);
        
        for(int ii=0; ii<nout; ii++){
          bool for_broken = false;
          
          while(getline(input_file, line)){
            get_tokens(line);
            
            string key = tokens[0];
            
            if(event.Event_numberP < n_particles){

              int index = event.Event_numberP;
              event.Event_numberP++;
              
              event.Particle_x[index]       = x;
              event.Particle_y[index]       = y;
              event.Particle_z[index]       = z;
              event.Particle_ctau[index]    = ctau;
              
              set_particle_variables(index);
              pvertex[index] = stoi(tokens[11]);
              
              if(ii < vertex[vbarcode].size()){
                vertex[vbarcode][ii] = index;
              }
            }
            for_broken = true;
            break;
          }
          if(!for_broken) return false;
        }
      }
      
      if(vertex.size() >= event.Event_numberV){
        for(int index=0; index<event.Event_numberP; index++){
          int code = pvertex[index];
          
          if(vertex.find(code) != vertex.end()){
            for(int i=0; i<n_daughters; i++){
              event.Particle_d[i][index] = vertex[code][i];
            }
          }
          else{
            for(int i=0; i<n_daughters; i++){
              event.Particle_d[i][index] = -1;
            }
          }
        }
        file->cd();
        tree->Fill();
        return true;
      }
    }
    if(for_line_broken) return false;
    
    return true;
  }
  
  void close(){
    tree->Write("", TObject::kOverwrite);
    file->Close();
  }
  
private:
  TFile *file;
  TTree *tree;
  Event event;
  vector<TBranch*> branches;
  int pvertex[n_particles] = {0};
  ifstream input_file;
  map<int, vector<int>> vertex;
  vector<string> tokens;
  
  void setup_branches(){
    tree->Branch("Event_numberP", &(event.Event_numberP), "Event_numberP/I");
    tree->Branch("Event_processID", &(event.Event_processID), "Event_processID/I");
    tree->Branch("Event_number", &(event.Event_number), "Event_number/I");
    tree->Branch("Event_numberMP", &(event.Event_numberMP), "Event_numberMP/I");
    tree->Branch("Event_scale", &(event.Event_scale), "Event_scale/F");
    tree->Branch("Event_alphaQCD", &(event.Event_alphaQCD), "Event_alphaQCD/F");
    tree->Branch("Event_alphaQED", &(event.Event_alphaQED), "Event_alphaQED/F");
    tree->Branch("Event_barcodeSPV", &(event.Event_barcodeSPV), "Event_barcodeSPV/I");
    tree->Branch("Event_numberV", &(event.Event_numberV), "Event_numberV/I");
    tree->Branch("Event_barcodeBP1", &(event.Event_barcodeBP1), "Event_barcodeBP1/I");
    tree->Branch("Event_barcodeBP2", &(event.Event_barcodeBP2), "Event_barcodeBP2/I");
    
    tree->Branch("Xsection_value", &(event.Xsection_value), "Xsection_value/F");
    tree->Branch("Xsection_error", &(event.Xsection_error), "Xsection_error/F");
    
    tree->Branch("PDF_parton1", &(event.PDF_parton1), "PDF_parton1/I");
    tree->Branch("PDF_parton2", &(event.PDF_parton2), "PDF_parton2/I");
    tree->Branch("PDF_x1", &(event.PDF_x1), "PDF_x1/F");
    tree->Branch("PDF_x2", &(event.PDF_x2), "PDF_x2/F");
    tree->Branch("PDF_Q2", &(event.PDF_Q2), "PDF_Q2/F");
    tree->Branch("PDF_x1f", &(event.PDF_x1f), "PDF_x1f/F");
    tree->Branch("PDF_x2f", &(event.PDF_x2f), "PDF_x2f/F");
    tree->Branch("PDF_id1", &(event.PDF_id1), "PDF_id1/I");
    tree->Branch("PDF_id2", &(event.PDF_id2), "PDF_id2/I");
    
    tree->Branch("Particle_x", &(event.Particle_x), makeBranchName("Particle_x", "F").c_str());
    tree->Branch("Particle_y", &(event.Particle_y), makeBranchName("Particle_y", "F").c_str());
    tree->Branch("Particle_z", &(event.Particle_z), makeBranchName("Particle_z", "F").c_str());
    
    tree->Branch("Particle_ctau", &(event.Particle_ctau), makeBranchName("Particle_ctau", "F").c_str());
    tree->Branch("Particle_barcode", &(event.Particle_barcode), makeBranchName("Particle_barcode", "I").c_str());
    tree->Branch("Particle_pid", &(event.Particle_pid), makeBranchName("Particle_pid", "I").c_str());
    
    tree->Branch("Particle_px", &(event.Particle_px), makeBranchName("Particle_px", "F").c_str());
    tree->Branch("Particle_py", &(event.Particle_py), makeBranchName("Particle_py", "F").c_str());
    tree->Branch("Particle_pz", &(event.Particle_pz), makeBranchName("Particle_pz", "F").c_str());
    tree->Branch("Particle_energy", &(event.Particle_energy), makeBranchName("Particle_energy", "F").c_str());
    tree->Branch("Particle_mass", &(event.Particle_mass), makeBranchName("Particle_mass", "F").c_str());
    tree->Branch("Particle_status", &(event.Particle_status), makeBranchName("Particle_status", "I").c_str());
    
    for(int i_daughter=0; i_daughter<n_daughters; i_daughter++){
      string branch_name = "Particle_d"+to_string(i_daughter);
      tree->Branch(branch_name.c_str(), &(event.Particle_d[i_daughter]), makeBranchName(branch_name, "I").c_str());
    }
  }
  
  void get_tokens(string line){
    tokens.clear();
    istringstream iss(line);
    string tmp;
    while(iss>>tmp) tokens.push_back(tmp);
  }
  
  void set_event_variables()
  {
    event.Event_number     = stoi(tokens[1]);
    event.Event_numberMP   = stoi(tokens[2]);
    event.Event_scale      = stod(tokens[3]);
    event.Event_alphaQCD   = stod(tokens[4]);
    event.Event_alphaQED   = stod(tokens[5]);
    event.Event_processID  = stoi(tokens[6]);
    event.Event_barcodeSPV = stoi(tokens[7]);
    event.Event_numberV    = stoi(tokens[8]);
    event.Event_barcodeBP1 = stoi(tokens[9]);
    event.Event_barcodeBP2 = stoi(tokens[10]);
    event.Event_numberP    = 0;
  }
  
  void set_xsec_variables()
  {
    event.Xsection_value = stod(tokens[1]);
    event.Xsection_error = stod(tokens[2]);
  }
  
  void set_pdf_variables()
  {
    event.PDF_parton1  = stoi(tokens[1]);
    event.PDF_parton2  = stoi(tokens[2]);
    event.PDF_x1       = stod(tokens[3]);
    event.PDF_x2       = stod(tokens[4]);
    event.PDF_Q2       = stod(tokens[5]);
    event.PDF_x1f      = stod(tokens[6]);
    event.PDF_x2f      = stod(tokens[7]);
    event.PDF_id1      = stoi(tokens[8]);
    event.PDF_id2      = stoi(tokens[9]);
  }
  
  void set_particle_variables(int index)
  {
    event.Particle_barcode[index] = stoi(tokens[1]);
    event.Particle_pid[index]     = stoi(tokens[2]);
    event.Particle_px[index]      = stod(tokens[3]);
    event.Particle_py[index]      = stod(tokens[4]);
    event.Particle_pz[index]      = stod(tokens[5]);
    event.Particle_energy[index]  = stod(tokens[6]);
    event.Particle_mass[index]    = stod(tokens[7]);
    event.Particle_status[index]  = stoi(tokens[8]);
  }
  
};

int main(int argc, char *argv[])
{
  if(argc <= 1){
    cout<<"Usage: ./hepmc2root.py <HepMC-file> [output root file = <name>.root]"<<endl;
    exit(0);
  }
  
  string file_name = argv[1];
  string output_file_name = "";
  
  if(argc == 3) output_file_name = argv[2];
  else{
    output_file_name = file_name.substr(file_name.find_last_of("/\\") + 1);
    output_file_name = std::regex_replace(output_file_name, std::regex(".hepmc"), ".root");
  }
  
  auto stream = new hepmc2root(file_name, output_file_name);
  
  int ii = 0;
  while(stream->process()){
    if(ii % 100 == 0) cout<<ii<<endl;
    ii++;
  }

  stream->close();
  
}
