import pandas as pd
import numpy as np
import sqlalchemy
from app import db
from app.utils import bp
from datetime import date, datetime

from flask import Blueprint, flash, render_template, request, redirect, url_for


@bp.route('/import', methods=['GET'])
def import_overview(entity = None):
    entity = request.args.get('entity',None)

    if not entity and entity in ["user","product","inventory"]:
        flash('Entity not found')
        return redirect(url_for('main.imexport_overview'))
    
    return render_template('import_index.html',entity = entity)

@bp.route('/import', methods=['POST'])
def upload_data(entity = None):
    global temp_ExcelData
    entity = request.args.get('entity',None)

    if not entity and entity in ["user","product","inventory"]:
        flash('Entity not found')
        return redirect(url_for('main.imexport_overview'))
    
    if not is_dbExist(entity):
        return redirect(url_for('main.imexport_overview'))
    try:
        excel_file = request.files['file']
        temp_ExcelData = pd.read_excel(excel_file)
        return redirect(url_for('utils.imexport_overview',entity = entity))
    except Exception as e:
        print(f"Error reading Excel file: {e}")

    
    return render_template('import_index.html',entity = entity)


temp_ExcelData = pd.DataFrame()
import_method=""
@bp.route('/<string:entity>/import/', methods=['GET','POST'])
def import_data(entity = None):
    global temp_ExcelData  #variable in import_utils.py
    global import_method
    info_message = ""
    
    if not entity is None and is_dbExist(entity):
        if not temp_ExcelData.empty or temp_ExcelData is not None:
            table = db.metadata.tables[entity]
            duplicate_rows, first_duplicate_rows, repeated_duplicate_rows = get_duplicate_rows_info(temp_ExcelData)
            
            column_types = [str(col.type.python_type) for col in table.columns]
            column_types.pop(0)
    
        return render_template('import_wizard.html', entity = entity,
                                    column_names=temp_ExcelData.columns.values, 
                                    first_duplicate_rows = first_duplicate_rows,
                                    repeated_rows = repeated_duplicate_rows,
                                    import_method = import_method,
                                    column_types=column_types,
                                    row_data=temp_ExcelData, zip=zip, info_message=info_message, pd=pd)
    else:
        return "Some errors occurred",404


@bp.route('/<string:entity>/file/upload', methods=['POST'])
def excel_upload(entity):
    global temp_ExcelData
    global import_method
    if not is_dbExist(entity):
        return "Some errors occurred",404
    if request.method == "POST":
        if import_method != "" or not import_method is None:
            import_method = ""
        try:
            excel_file = request.files['file']
            temp_ExcelData = pd.read_excel(excel_file)
            return redirect(url_for('stock.import_stock'))
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            # return None
            return redirect(url_for('utils.import_data',entity=entity))
    

@bp.route('/<string:entity>/file/validate', methods=['POST'])
def validate_exceldata(entity):
    global temp_ExcelData
    global import_method

    if not is_dbExist(entity): return "Some errors occurred",404
    
    if request.method == "POST":
        if import_method != "" or not import_method is None:
            import_method = ""
        temp_ExcelData = data_toDataFrame(request, 'column_names')
        temp_ExcelData = down_castDF(temp_ExcelData)
        print(temp_ExcelData.dtypes)
        check_duplicate_rows(temp_ExcelData)
            # info_message += "Data contains duplicate rows, are you sure you want to keep them in the record? "

        #  Step 2:Check for empty values
        check_empty_values(temp_ExcelData)
            # info_message += "Warning: There are NaN/Empty values in the DataFrame. Please review the data. (X) \n"
        print("before return: ",temp_ExcelData)
    
        return redirect(url_for('utils.import_data',entity = entity))

@bp.route('/<string:entity>/file/final_validate', methods=['POST'])
def final_validate(entity):
    global temp_ExcelData
    global import_method

    if not is_dbExist(entity): return "Some error occurred",404
    if request.method == "POST":
        custom_Table = db.metadata.tables[entity]
        # temp_ExcelData = down_castDF(data)

        import_method = check_Import_condition(temp_ExcelData,custom_Table)
        check_writability_and_print(temp_ExcelData,entity)
        temp_ExcelData = temp_ExcelData
        return redirect(url_for('utils.import_data',entity=entity))



# FUNCTIONS

def excel_upload(excel_file):
    # global temp_ExcelData
    # global import_method
    try:
        temp_ExcelData = pd.read_excel(excel_file)
        return temp_ExcelData
    
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None
    
def is_dbExist(table_name):
    try:
        db.session.execute(db.select(db.metadata.tables[table_name]))
        return True
    except Exception as e:
        return False



def check_Import_condition(df_data,db_data,custom_model=False):
    global import_method
    # there is 3 return conditions: Smart import/ Custom-Advance Import and Import Failure
    df_columns = df_data.columns
    db_columns = [ column for column in db_data.columns.keys() if column not in "id"]
    db_types = [col.type.python_type for col in db_data.columns]
    db_types.pop(0)
    
    #convert DF data types to DB datatype first
    converted_dftypes = converto_dbtypes(df_data)
    
    # Condition Checking
    if len(df_columns) == len(db_columns) and list(set(db_types)) == list(set(converted_dftypes)):
        if (list(df_columns) == list(db_columns)):
            #"Perfect match (Smart Import)"
            import_method = "smart"
        else:
            #"Advance import (Custom/Advance Import) 1: all ok but column names not same; just change name to DB_column names"
            import_method = "smart"

    elif len(df_columns) == len(db_columns) and list(set(converted_dftypes)) >= list(set(db_types)):
        # "Advance import (Custom/Advance Import) 2: length of columns same but df_types >= dbtypes "
        import_method = "advance"

    elif len(df_columns) >= len(db_columns) and list(set(converted_dftypes)) >= list(set(db_types)):
       # "Advance import (Custom/Advance Import) 3: df_columns >= dbcolumns, but list of dftype >= dbtype"
        import_method = "advance"

    elif all(element in converted_dftypes for element in db_types):
        # "Advance import (Custom/Advance Import) 4: last compare data type got in db"
        import_method = "advance"

    if len(list(set(db_types))) > len(list(set(converted_dftypes))) and len(db_columns) > len(df_columns):
        print("Import failed (Import Failure)")
        import_method = "failure"
    return import_method

@bp.route('/<string:entity>/file/insert_values', methods=['POST'])
def insert_toDB(entity):
    global temp_ExcelData
    global import_method
    print(import_method)
    table = db.metadata.tables[entity]
    db_columns = [column for column in table.columns.keys() if column not in "id"]

    if not is_dbExist(entity): return "Some error occurred",404
    if request.method == "POST":
        if import_method == "smart":
            # Replace column name of temp_data
            temp_ExcelData.columns = db_columns
            data = temp_ExcelData
            
        elif import_method == "advance":
            selected_df_column = request.form.getlist("column_index")
            data = temp_ExcelData[selected_df_column]
            data.columns = db_columns
            print(data)

        if check_writability_and_print(data,entity):
            db.session.execute(table.insert(),data.to_dict(orient='records'))
            db.session.commit()
            return redirect(url_for(f'{entity}.index'))
        else:
            import_method = "failure"

    return redirect(url_for('utils.import_data',entity=entity))






# CHECKING SERIES #
def check_empty_values(data):
    for col in data.columns:
        # data[col] = data[col].apply(lambda x: pd.NA if pd.isna(x) or (not x or x.isspace()) else x)
        data[col] = data[col].apply(lambda x: np.nan if isinstance(x, str) and (x.isspace() or not x) else x)
    print(data)
    if data.isnull().values.any():
        print("Warning: There are NaN/Empty values in the DataFrame. Please review the data. (X)")
        return False

    print("NaN/null value: Not Detected (/)")
    return True

def check_duplicate_rows(data):
    duplicate_rows = data[data.duplicated(keep=False)]
    print(duplicate_rows)

    if duplicate_rows.empty:
        return True
    
    return False

def check_column_number(data, column_names):
    if not len(list(data)) >= len(column_names):
        print("The number of data columns does not match the table columns. (X)")
        return False
    
    print("Table column: More than or equal to DB columns (/)") 
    return True

def check_column_names(data, column_names):
    if not column_names == list(data):
        print("The columns name does not match the DB columns. (X)")
        return False
    
    print("Column Name: Matched (/)")
    return True

def check_data_types(data, db_column_types):
    data_types = convert_PDtypes(data, db_column_types)
    if not compare_data_types(db_column_types, data_types):
        print("Data types in DataFrame do not match with SQLAlchemy model. (X)")
        return False
    
    print("Data Type: Matched (/)")
    return True



def check_writability_and_print(data,entity):
    result, error_message = check_writability(data,entity)
    if not result:
        print("Error: Data cannot be written to the database. ", error_message)
        return False
    
    print("Congratulation! Data can be written to the database. (/)")
    return True


def data_toDataFrame(request,col_names):
    columns = list(request.form.getlist(col_names))
    data = {}
    for col in columns:
        data[col] = request.form.getlist(col)
        print(True in [not v or v.isspace() for v in data[col]])
        

    df = pd.DataFrame(data)
    print("df:",df)
    return df



def check_writability(df,entity):
    try:
        listToWrite = df.to_dict(orient='records')

        metadata = db.metadata
        table = sqlalchemy.Table(entity, metadata, autoload=True)
        db.session.execute(table.insert(), listToWrite)
    except Exception as e:
        db.session.rollback()
        return False, str(e)
    db.session.rollback()  # Rollback even if successful
    return True, None
    # USE 
    # result, error_message = check_writability(data)
    # if result:
    #     print("Data can be written to the database")
    # else:
    #     print("Error: Data cannot be written to the database.", error_message)


def get_duplicate_rows_info(data):
    duplicate_rows = data[data.duplicated(keep=False)]
    first_duplicate_rows = duplicate_rows[~duplicate_rows.duplicated(keep='first')]
    repeated_duplicate_rows = duplicate_rows[duplicate_rows.duplicated()]
    return duplicate_rows, first_duplicate_rows, repeated_duplicate_rows


def down_castDF(df_data):
    # downcasted = df_data.apply(pd.to_numeric, errors='ignore')
    # downcasted = df_data.apply(pd.to_datetime, errors='ignore')
    # print("Down Casted after Validation: \n",downcasted)
    # print("Down Casted after Validation type: \n",downcasted.dtypes)

    # Downcast numeric columns to appropriate types
   # Automatic downcast of numeric columns
    for col in df_data.columns:
        if pd.to_datetime(df_data[col],yearfirst=True, errors='coerce').notna().all():
            df_data[col] = pd.to_datetime(df_data[col],yearfirst=True, errors='coerce')
        elif pd.to_numeric(df_data[col], errors='coerce').notna().all():
            df_data[col] = pd.to_numeric(df_data[col], errors='coerce', downcast='integer')
            if df_data[col].dtype == 'int8':
                df_data[col] = df_data[col].astype('int64')
    # print("Down Casted after Validation: \n",df_data)
    # print("Down Casted after Validation type: \n",df_data.dtypes)
    return df_data


def converto_dbtypes(df_data):
    #This method uses after downcasting dataframe; only dataframe as parameters

    converted_type = []
    for col in df_data:
        if str(df_data[col].dtype) == 'int64':
            converted_type.append(int)
        elif str(df_data[col].dtype) == 'float64':
            converted_type.append(float)
        elif str(df_data[col].dtype) == 'object':
            converted_type.append(str)
        elif str(df_data[col].dtype) == 'datetime64[ns]':
            converted_type.append(date)
    

    # print("converted_type",converted_type)
    return converted_type

def compare_data_types(expected, actual):
    checked_type = []
    for exp, act in zip(expected, actual):
        if exp == str and act == 'object':
            checked_type.append(True)
            continue
        elif exp == date and act == 'datetime64[ns]':
            checked_type.append(True)
            continue
        elif exp == float and act == "float64":
            checked_type.append(True)
            continue
        elif exp == int and act == "int32":
            checked_type.append(True)
            continue
        else:
            checked_type.append(False)

    return all(checked_type)




def convert_PDtypes(DataFrame = [], db_column_types = []):
    """
    ### Convert columns to expected data types
    ~Method Type: Custom~
    \n\n
    convert_PDtypes(DataFrame = [], db_column_types = [] )

    DataFrame = List | pd.DataFrame() \n
    db_column_types = List | pd.DataFrame() \n
    ### Example:
    \n\n
      convert_PDtypes([ object,object,int64,float64 ], [str,str,int,float] ) \ 
      \ 
      \ 
      \\n
        Note!!!: this method onsidering removal
    """

    for col, expected_type in zip(DataFrame.columns, db_column_types):
        if expected_type == date:
            DataFrame[col] = parse_date(DataFrame[col])
        else:
            DataFrame[col] = DataFrame[col].astype(float) if expected_type == float else DataFrame[col].astype(expected_type)
    return DataFrame.dtypes

def parse_date(df_column):
    try:
        df_column = pd.to_datetime(df_column,yearfirst=True, errors='coerce')
    except ValueError:
        pass

    return df_column

            # Get columns name: Stock.__table__.c or Stock.metadata.tables['stock'].columns.keys()
            # Get columns type: Stock.__table__.c[col].type.python_type