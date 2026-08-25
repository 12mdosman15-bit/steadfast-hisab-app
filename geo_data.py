# -*- coding: utf-8 -*-
"""Bangladesh district -> upazila/thana data for Steadfast Business হিসাব.

This file is used by app.py:
    from geo_data import BD_GEO

BD_GEO maps each district name to a list of upazila/thana names.
Checked against the current Bangladesh National Portal administrative list.
"""

BD_GEO = {

    'Dhaka': [
        'Dhamrai', 'Dohar', 'Keraniganj', 'Nawabganj', 'Savar',

        # Dhaka Metropolitan Police (DMP) Thanas
        'Adabor', 'Airport', 'Badda', 'Banani', 'Bangshal',
        'Bhashantek', 'Cantonment', 'Chawkbazar', 'Dakshinkhan',
        'Darus Salam', 'Demra', 'Dhanmondi', 'Gandaria', 'Gulshan',
        'Hatirjheel', 'Hazaribagh', 'Jatrabari', 'Kadamtali', 'Kafrul',
        'Kalabagan', 'Kamrangirchar', 'Khilgaon', 'Khilkhet', 'Kotwali',
        'Lalbagh', 'Mirpur Model', 'Mohammadpur', 'Motijheel', 'Mugda',
        'New Market', 'Pallabi', 'Paltan', 'Ramna', 'Rampura',
        'Rupnagar', 'Sabujbagh', 'Shah Ali', 'Shahbagh', 'Shahjahanpur',
        'Sher-e-Bangla Nagar', 'Shyampur', 'Sutrapur', 'Tejgaon',
        'Tejgaon Industrial Area', 'Turag', 'Uttarkhan', 'Uttara East',
        'Uttara West', 'Vatara', 'Wari'
    ],

    'Faridpur': [
        'Alfadanga', 'Bhanga', 'Boalmari', 'Charbhadrasan',
        'Faridpur Sadar', 'Madhukhali', 'Nagarkanda', 'Sadarpur', 'Saltha'
    ],

    'Gazipur': [
        'Gazipur Sadar', 'Kaliakair', 'Kaliganj', 'Kapasia', 'Sreepur'
    ],

    'Gopalganj': [
        'Gopalganj Sadar', 'Kashiani', 'Kotalipara',
        'Muksudpur', 'Tungipara'
    ],

    'Kishoreganj': [
        'Ashtagram', 'Bajitpur', 'Bhairab', 'Hossainpur', 'Itna',
        'Karimganj', 'Katiadi', 'Kishoreganj Sadar', 'Kuliarchar',
        'Mithamain', 'Nikli', 'Pakundia', 'Tarail'
    ],

    'Madaripur': [
        'Kalkini', 'Madaripur Sadar', 'Rajoir', 'Shibchar', 'Dasar'
    ],

    'Manikganj': [
        'Daulatpur', 'Ghior', 'Harirampur', 'Manikganj Sadar',
        'Saturia', 'Shibalaya', 'Singair'
    ],

    'Munshiganj': [
        'Gazaria', 'Lohajang', 'Munshiganj Sadar',
        'Sirajdikhan', 'Sreenagar', 'Tongibari'
    ],

    'Narayanganj': [
        'Araihazar', 'Sonargaon', 'Narayanganj Sadar',
        'Rupganj', 'Bandar'
    ],

    'Narsingdi': [
        'Belabo', 'Monohardi', 'Narsingdi Sadar',
        'Palash', 'Raipura', 'Shibpur'
    ],

    'Rajbari': [
        'Baliakandi', 'Goalanda', 'Kalukhali',
        'Pangsha', 'Rajbari Sadar'
    ],

    'Shariatpur': [
        'Bhedarganj', 'Damudya', 'Gosairhat',
        'Naria', 'Shariatpur Sadar', 'Zajira'
    ],

    'Tangail': [
        'Basail', 'Bhuapur', 'Delduar', 'Dhanbari',
        'Ghatail', 'Gopalpur', 'Kalihati', 'Madhupur',
        'Mirzapur', 'Nagarpur', 'Sakhipur', 'Tangail Sadar'
    ],

    'Bagerhat': [
        'Chitalmari', 'Fakirhat', 'Kachua', 'Mollahat',
        'Mongla', 'Morrelganj', 'Rampal', 'Sharankhola',
        'Bagerhat Sadar'
    ],

    'Chuadanga': [
        'Alamdanga', 'Chuadanga Sadar', 'Damurhuda', 'Jibannagar'
    ],

    'Jashore': [
        'Abhaynagar', 'Bagherpara', 'Chaugachha', 'Jhikargachha',
        'Keshabpur', 'Jashore Sadar', 'Manirampur', 'Sharsha'
    ],

    'Jhenaidah': [
        'Harinakunda', 'Jhenaidah Sadar', 'Kaliganj',
        'Kotchandpur', 'Maheshpur', 'Shailkupa'
    ],

    'Khulna': [
        'Batiaghata', 'Dacope', 'Dumuria', 'Koyra',
        'Paikgachha', 'Phultala', 'Rupsa', 'Terokhada', 'Dighalia'
    ],

    'Kushtia': [
        'Bheramara', 'Daulatpur', 'Khoksa', 'Kumarkhali',
        'Kushtia Sadar', 'Mirpur'
    ],

    'Magura': [
        'Magura Sadar', 'Mohammadpur', 'Shalikha', 'Sreepur'
    ],

    'Meherpur': [
        'Gangni', 'Mujibnagar', 'Meherpur Sadar'
    ],

    'Narail': [
        'Kalia', 'Lohagara', 'Narail Sadar'
    ],

    'Satkhira': [
        'Assasuni', 'Debhata', 'Kalaroa', 'Kaliganj',
        'Satkhira Sadar', 'Shyamnagar', 'Tala'
    ],

    'Bandarban': [
        'Alikadam', 'Bandarban Sadar', 'Lama',
        'Naikhongchhari', 'Rowangchhari', 'Ruma', 'Thanchi'
    ],

    'Brahmanbaria': [
        'Akhaura', 'Ashuganj', 'Bancharampur', 'Bijoynagar',
        'Brahmanbaria Sadar', 'Kasba', 'Nabinagar',
        'Nasirnagar', 'Sarail'
    ],

    'Chandpur': [
        'Chandpur Sadar', 'Faridganj', 'Haimchar', 'Hajiganj',
        'Kachua', 'Matlab South', 'Matlab North', 'Shahrasti'
    ],

    'Chattogram': [
        'Anwara', 'Banshkhali', 'Boalkhali', 'Chandanaish',
        'Fatikchhari', 'Hathazari', 'Lohagara', 'Mirsharai',
        'Patiya', 'Rangunia', 'Raozan', 'Sandwip',
        'Satkania', 'Sitakunda', 'Karnaphuli'
    ],

    'Cumilla': [
        'Barura', 'Brahmanpara', 'Burichang', 'Chandina',
        'Chauddagram', 'Adarsha Sadar', 'Sadar South',
        'Daudkandi', 'Debidwar', 'Homna', 'Laksam',
        'Monoharganj', 'Meghna', 'Muradnagar', 'Nangalkot',
        'Titas', 'Lalmai'
    ],

    'Coxs Bazar': [
        'Chakaria', 'Coxs Bazar Sadar', 'Kutubdia', 'Maheshkhali',
        'Pekua', 'Ramu', 'Teknaf', 'Ukhia', 'Eidgaon'
    ],

    'Feni': [
        'Chhagalnaiya', 'Daganbhuiyan', 'Feni Sadar',
        'Fulgazi', 'Parshuram', 'Sonagazi'
    ],

    'Khagrachhari': [
        'Dighinala', 'Manikchhari', 'Khagrachhari Sadar',
        'Lakshmichhari', 'Mahalchhari', 'Matiranga',
        'Panchhari', 'Ramgarh', 'Guimara'
    ],

    'Lakshmipur': [
        'Kamalnagar', 'Lakshmipur Sadar', 'Raipur',
        'Ramganj', 'Ramgati', 'Chandraganj'
    ],

    'Noakhali': [
        'Begumganj', 'Chatkhil', 'Companiganj', 'Hatiya',
        'Kabirhat', 'Senbagh', 'Sonaimuri',
        'Subarnachar', 'Noakhali Sadar'
    ],

    'Rangamati': [
        'Baghaichhari', 'Barkal', 'Kawkhali', 'Kaptai',
        'Juraichhari', 'Langadu', 'Naniarchar',
        'Rangamati Sadar', 'Rajasthali', 'Bilaichhari'
    ],

    'Bogura': [
        'Adamdighi', 'Bogura Sadar', 'Dhunat', 'Dupchanchia',
        'Gabtali', 'Kahaloo', 'Nandigram', 'Sariakandi',
        'Shajahanpur', 'Sherpur', 'Shibganj', 'Sonatala',
        'Mokamtala'
    ],

    'Joypurhat': [
        'Akkelpur', 'Joypurhat Sadar', 'Kalai',
        'Panchbibi', 'Khetlal'
    ],

    'Naogaon': [
        'Atrai', 'Dhamoirhat', 'Manda', 'Mahadevpur',
        'Naogaon Sadar', 'Niamatpur', 'Patnitala',
        'Raninagar', 'Sapahar', 'Badalgachhi', 'Porsha'
    ],

    'Natore': [
        'Bagatipara', 'Baraigram', 'Gurudaspur',
        'Lalpur', 'Natore Sadar', 'Singra', 'Naldanga'
    ],

    'Chapainawabganj': [
        'Shibganj', 'Bholahat', 'Gomastapur',
        'Nachole', 'Chapainawabganj Sadar'
    ],

    'Pabna': [
        'Atgharia', 'Bera', 'Bhangura', 'Chatmohar',
        'Faridpur', 'Ishwardi', 'Pabna Sadar',
        'Santhia', 'Sujanagar'
    ],

    'Rajshahi': [
        'Bagha', 'Bagmara', 'Charghat', 'Durgapur',
        'Godagari', 'Mohanpur', 'Paba', 'Puthia', 'Tanore'
    ],

    'Sirajganj': [
        'Belkuchi', 'Chauhali', 'Kamarkhanda', 'Kazipur',
        'Raiganj', 'Shahjadpur', 'Sirajganj Sadar',
        'Tarash', 'Ullapara'
    ],

    'Habiganj': [
        'Ajmiriganj', 'Bahubal', 'Baniachong', 'Chunarughat',
        'Habiganj Sadar', 'Lakhai', 'Madhabpur',
        'Nabiganj', 'Shayestaganj'
    ],

    'Moulvibazar': [
        'Barlekha', 'Juri', 'Kamalganj', 'Kulaura',
        'Moulvibazar Sadar', 'Rajnagar', 'Sreemangal'
    ],

    'Sunamganj': [
        'Bishwambharpur', 'Chhatak', 'Derai', 'Dharmapasha',
        'Dowarabazar', 'Jagannathpur', 'Jamalganj',
        'Shalla', 'Sunamganj Sadar', 'Tahirpur',
        'Shantiganj', 'Madhyanagar'
    ],

    'Sylhet': [
        'Balaganj', 'Beanibazar', 'Bishwanath',
        'Companiganj', 'Dakshin Surma', 'Fenchuganj',
        'Golapganj', 'Gowainghat', 'Jaintiapur',
        'Kanaighat', 'Sylhet Sadar', 'Zakiganj', 'Osmani Nagar'
    ],

    'Dinajpur': [
        'Birampur', 'Birganj', 'Biral', 'Bochaganj',
        'Chirirbandar', 'Phulbari', 'Ghoraghat', 'Hakimpur',
        'Kaharole', 'Khansama', 'Nawabganj',
        'Parbatipur', 'Dinajpur Sadar'
    ],

    'Gaibandha': [
        'Phulchhari', 'Gaibandha Sadar', 'Gobindaganj',
        'Palashbari', 'Sadullapur', 'Saghatta', 'Sundarganj'
    ],

    'Kurigram': [
        'Phulbari', 'Bhurungamari', 'Char Rajibpur',
        'Chilmari', 'Kurigram Sadar', 'Nageshwari',
        'Rajarhat', 'Rowmari', 'Ulipur'
    ],

    'Lalmonirhat': [
        'Aditmari', 'Hatibandha', 'Kaliganj',
        'Lalmonirhat Sadar', 'Patgram'
    ],

    'Nilphamari': [
        'Domar', 'Jaldhaka', 'Kishoreganj',
        'Nilphamari Sadar', 'Saidpur', 'Dimla'
    ],

    'Panchagarh': [
        'Atwari', 'Boda', 'Debiganj',
        'Panchagarh Sadar', 'Tetulia'
    ],

    'Rangpur': [
        'Badarganj', 'Kaunia', 'Rangpur Sadar',
        'Mithapukur', 'Pirganj', 'Pirganj',
        'Taraganj', 'Gangachara'
    ],

    'Thakurgaon': [
        'Pirganj', 'Baliadangi', 'Haripur',
        'Ranisankail', 'Thakurgaon Sadar',
        'Bhulli', 'Ruhia'
    ],

    'Jamalpur': [
        'Bakshiganj', 'Dewanganj', 'Islampur',
        'Jamalpur Sadar', 'Madarganj', 'Melandaha',
        'Sarishabari'
    ],

    'Mymensingh': [
        'Bhaluka', 'Dhobaura', 'Phulpur', 'Gaffargaon',
        'Gauripur', 'Haluaghat', 'Ishwarganj',
        'Mymensingh Sadar', 'Muktagachha', 'Nandail',
        'Phulpur', 'Tarakanda', 'Trishal'
    ],

    'Netrokona': [
        'Atpara', 'Barhatta', 'Durgapur', 'Khaliajuri',
        'Kalmakanda', 'Kendua', 'Madan', 'Mohanganj',
        'Netrokona Sadar', 'Purbadhala'
    ],

    'Sherpur': [
        'Jhenaigati', 'Nakla', 'Nalitabari',
        'Sherpur Sadar', 'Sreebardi'
    ],

    'Barguna': [
        'Amtali', 'Bamna', 'Barguna Sadar',
        'Betagi', 'Patharghata', 'Taltali'
    ],

    'Barishal': [
        'Agailjhara', 'Babuganj', 'Bakerganj', 'Banaripara',
        'Gournadi', 'Hizla', 'Barishal Sadar',
        'Mehendiganj', 'Muladi', 'Wazirpur'
    ],

    'Bhola': [
        'Bhola Sadar', 'Borhanuddin', 'Daulatkhan',
        'Lalmohan', 'Manpura', 'Tazumuddin', 'Char Fasson'
    ],

    'Jhalokathi': [
        'Jhalokathi Sadar', 'Nalchity', 'Kathalia', 'Rajapur'
    ],

    'Patuakhali': [
        'Bauphal', 'Dashmina', 'Dumki', 'Kalapara',
        'Mirzaganj', 'Patuakhali Sadar',
        'Rangabali', 'Galachipa'
    ],

    'Pirojpur': [
        'Bhandaria', 'Kawkhali', 'Mathbaria', 'Nazirpur',
        'Pirojpur Sadar', 'Nesarabad', 'Indurkani'
    ]
}
__all__ = ['BD_GEO']
