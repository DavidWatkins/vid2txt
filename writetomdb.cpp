#include <stdio.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <chrono>
#include <thread>
#include <stdlib.h>     /* atoi */
#include <process.h>

//g++ writetomdb.cpp -std=gnu++0x

using namespace std;

int main(int argc, char** argv) {
	if(argc <5) {
		exit(0);
	}
	int num_frames = atoi(argv[1]);
	std::chrono::duration<double> dur(atof(argv[2]));
	auto frame_interval = std::chrono::duration_cast<std::chrono::milliseconds>(dur);
	// int fps = atoi(argv[3]);
	string mdba = argv[4];
	string mdbl = argv[5];
	string video_file_name = argv[6];
	string out_dir = argv[7];

	for(int i = 0; i < num_frames; ++i) {
		ifstream myfile;
		char snum[30];
		sprintf(snum, "%d", i);
		myfile.open(out_dir + video_file_name + ".frame" + snum + ".txt");
		std::string line;

		cout << "Writing frame " << i << std::endl;

		while (std::getline(myfile, line))
		{
			string name = line.substr(0, 14);
			string msg = line.substr(15, 24);

			procxx::process mdb{mdba, mdbl};
			mdb.exec();
			std::string line;
			std::getline(mdb.output(), line);
		    std::cout << line << std::endl;
			mdb << name << "\n";
			std::getline(mdb.output(), line);
		    std::cout << line << std::endl;
			mdb << msg << "\n";
			mdb.close(procxx::pipe_t::write_end());

			// FILE *out;
			// if(!(out = popen((mdba + " " + mdbl).c_str(), "w"))){
			// 	return 1;
			// }

			// fputs(name.c_str(), out);
			// fputs(msg.c_str(), out);

			// pclose(out);

		}

		cout << "Wrote frame" << std::endl;

		std::this_thread::sleep_for(frame_interval);

		myfile.close();
	}

}